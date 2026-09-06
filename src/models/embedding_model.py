"""
src/models/embedding_model.py
Semantic embedding model for CV–Job matching.

Backend hierarchy:
  1. SentenceTransformer (best quality — requires sentence-transformers package)
  2. _LocalEmbeddingBackend (HashingVectorizer fallback — no sentence-transformers)

Default English model: all-MiniLM-L6-v2
  * Stable on Python 3.13 + Windows
  * Already cached on disk from first install
  * Upgrade to all-mpnet-base-v2 via EMBEDDING_MODEL_EN in .env
    (requires model download; may require Python ≤3.12 for threaded loading)

Multilingual: paraphrase-multilingual-mpnet-base-v2 (unchanged — best in class).
"""
from __future__ import annotations

import os
# Prevent HuggingFace tokenizer from spawning extra threads (crashes Python 3.13 on Windows)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


import hashlib
import logging
from functools import lru_cache
from typing import Dict, Iterable, List

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from src.parsing.parser import segment_cv

from .base_model import BaseMatchingModel

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None
    _ST_AVAILABLE = False

# Read model names from config if available, else use safe defaults.
# Default is all-MiniLM-L6-v2 — stable on Python 3.13 + Windows.
# Set EMBEDDING_MODEL_EN=all-mpnet-base-v2 in .env for the higher-accuracy model
# (requires model to be pre-downloaded and Python ≤3.12 recommended).
try:
    from src.config import settings as _cfg
    _MODEL_EN = _cfg.EMBEDDING_MODEL_EN   # default: "all-MiniLM-L6-v2"
    _MODEL_ML = _cfg.EMBEDDING_MODEL_ML   # default: "paraphrase-multilingual-mpnet-base-v2"
except Exception:
    _MODEL_EN = "all-MiniLM-L6-v2"
    _MODEL_ML = "paraphrase-multilingual-mpnet-base-v2"


# ─────────────────────────────────────────────
# Backends
# ─────────────────────────────────────────────

class _LocalEmbeddingBackend:
    """
    HashingVectorizer fallback when sentence-transformers is not installed.
    Significantly lower accuracy — logged as a warning on first use.
    """

    _warned: bool = False

    def __init__(self) -> None:
        if not _LocalEmbeddingBackend._warned:
            logger.warning(
                "sentence-transformers is not installed. "
                "EmbeddingMatcher is using the HashingVectorizer fallback, "
                "which provides MUCH lower accuracy. "
                "Install with: pip install sentence-transformers"
            )
            _LocalEmbeddingBackend._warned = True

        self.word_vectorizer = HashingVectorizer(
            n_features=2048,          # doubled from 1024 for better coverage
            analyzer="word",
            ngram_range=(1, 2),
            alternate_sign=False,
            norm="l2",
        )
        self.char_vectorizer = HashingVectorizer(
            n_features=2048,
            analyzer="char_wb",
            ngram_range=(3, 5),
            alternate_sign=False,
            norm="l2",
        )

    def encode(self, texts: List[str]) -> np.ndarray:
        word_matrix = self.word_vectorizer.transform(texts)
        char_matrix = self.char_vectorizer.transform(texts)
        matrix = hstack([word_matrix, char_matrix]).astype(float)
        return normalize(matrix).toarray()


class _SentenceTransformerBackend:
    """Sentence-Transformers backend (preferred)."""

    def __init__(self, model_name: str) -> None:
        logger.info("Loading SentenceTransformer model: %s", model_name)
        print(f"DEBUG SentenceTransformer is {type(SentenceTransformer)}")
        self.model_name = model_name
        # low_cpu_mem_usage=False disables the transformers 4.47+ threaded model
        # materialiser (core_model_loading.py) which crashes on Python 3.13 + Windows.
        # Without it, transformers uses concurrent.futures to load weights — unstable.
        self.model = SentenceTransformer(
            model_name,
            model_kwargs={"low_cpu_mem_usage": False},
        )
        logger.info("SentenceTransformer model loaded: %s", model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )


# ─────────────────────────────────────────────
# Cache key helper
# ─────────────────────────────────────────────

def _cache_key(text: str, backend_key: str) -> str:
    return f"{backend_key}:{hashlib.md5((text or '').encode('utf-8')).hexdigest()}"


# ─────────────────────────────────────────────
# EmbeddingMatcher
# ─────────────────────────────────────────────

class EmbeddingMatcher(BaseMatchingModel):
    """
    Semantic similarity matcher using dual SentenceTransformer backends.

    English model  : all-mpnet-base-v2
    Multilingual   : paraphrase-multilingual-mpnet-base-v2

    Scoring strategy:
        base_score    = 0.5 * english_similarity + 0.5 * multilingual_similarity
        section_score = weighted section-aware similarity (experience-heavy)
        final         = 0.7 * base_score + 0.3 * section_score
    """

    _MAX_CACHE_ENTRIES = 8192  # Increased to prevent thrashing during cross-validation

    def __init__(self) -> None:
        self.model_names = {
            "english":       _MODEL_EN,
            "multilingual":  _MODEL_ML,
        }
        self.backends: Dict[str, object] = {
            "english":      self._build_backend(self.model_names["english"]),
            "multilingual": self._build_backend(self.model_names["multilingual"]),
        }
        self._cache: Dict[str, np.ndarray] = {}

    @staticmethod
    def _build_backend(model_name: str):
        if not _ST_AVAILABLE:
            return _LocalEmbeddingBackend()
        try:
            return _SentenceTransformerBackend(model_name)
        except Exception as exc:
            logger.warning(
                "Failed to load SentenceTransformer '%s': %s. "
                "Falling back to HashingVectorizer.",
                model_name, exc,
            )
            return _LocalEmbeddingBackend()

    def _encode_text(self, text: str, backend_key: str) -> np.ndarray:
        key = _cache_key(text, backend_key)

        # Evict oldest entries if cache is full (simple FIFO eviction)
        if len(self._cache) >= self._MAX_CACHE_ENTRIES and key not in self._cache:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        if key not in self._cache:
            self._cache[key] = self.backends[backend_key].encode([text or ""])[0]
        return self._cache[key]

    def _similarity(self, text_a: str, text_b: str, backend_key: str) -> float:
        vec_a = self._encode_text(text_a, backend_key).reshape(1, -1)
        vec_b = self._encode_text(text_b, backend_key).reshape(1, -1)
        return float(np.clip(cosine_similarity(vec_a, vec_b)[0, 0], 0.0, 1.0))

    def section_aware_similarity(self, cv_sections: Dict[str, str], job_text: str) -> float:
        """
        Compute a weighted similarity across CV sections.
        Experience and skills are weighted most heavily for recruitment relevance.
        """
        weights = {
            "experience":    0.40,   # most important for seniority assessment
            "skills":        0.30,   # direct keyword and technology match
            "summary":       0.15,   # professional self-description
            "education":     0.10,   # degree / institution relevance
            "languages":     0.05,   # linguistic capabilities
        }
        weighted_scores: List[float] = []
        total_weight_used = 0.0
        for section, weight in weights.items():
            content = cv_sections.get(section, "")
            if not content:
                continue
            section_score = (
                0.5 * self._similarity(content, job_text, "english")
                + 0.5 * self._similarity(content, job_text, "multilingual")
            )
            weighted_scores.append(weight * section_score)
            total_weight_used += weight
            
        final_score = sum(weighted_scores) / total_weight_used if total_weight_used > 0 else 0.0
        return float(np.clip(final_score, 0.0, 1.0))

    def predict(self, cv: str, job: str) -> float:
        """Return overall similarity score in [0, 1]."""
        base_score = (
            0.5 * self._similarity(cv, job, "english")
            + 0.5 * self._similarity(cv, job, "multilingual")
        )
        section_score = self.section_aware_similarity(segment_cv(cv), job)
        return float(np.clip(0.7 * base_score + 0.3 * section_score, 0.0, 1.0))

    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[float]:
        cv_list  = list(cvs)
        job_list = list(jobs)
        if len(cv_list) != len(job_list):
            raise ValueError("CV and job lists must have the same length.")
            
        # Optimization: Pre-extract all unique texts to batch-encode them
        unique_texts = set()
        for cv, job in zip(cv_list, job_list):
            unique_texts.add(cv)
            unique_texts.add(job)
            sections = segment_cv(cv)
            for content in sections.values():
                if content:
                    unique_texts.add(content)
        
        # Batch encode for English backend
        texts_to_encode_en = [t for t in unique_texts if _cache_key(t, "english") not in self._cache]
        if texts_to_encode_en:
            embeddings_en = self.backends["english"].encode(texts_to_encode_en)
            for t, emb in zip(texts_to_encode_en, embeddings_en):
                self._cache[_cache_key(t, "english")] = emb
                
        # Batch encode for Multilingual backend
        texts_to_encode_ml = [t for t in unique_texts if _cache_key(t, "multilingual") not in self._cache]
        if texts_to_encode_ml:
            embeddings_ml = self.backends["multilingual"].encode(texts_to_encode_ml)
            for t, emb in zip(texts_to_encode_ml, embeddings_ml):
                self._cache[_cache_key(t, "multilingual")] = emb
                
        return [self.predict(cv, job) for cv, job in zip(cv_list, job_list)]
