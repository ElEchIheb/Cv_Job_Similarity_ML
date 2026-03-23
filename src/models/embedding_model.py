from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from src.parsing.parser import segment_cv

from .base_model import BaseMatchingModel

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    SentenceTransformer = None


class _LocalEmbeddingBackend:
    def __init__(self) -> None:
        self.word_vectorizer = HashingVectorizer(
            n_features=1024,
            analyzer="word",
            ngram_range=(1, 2),
            alternate_sign=False,
            norm="l2",
        )
        self.char_vectorizer = HashingVectorizer(
            n_features=1024,
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


class _SentenceTransformerBackend:  # pragma: no cover - depends on optional dependency
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True))


class EmbeddingMatcher(BaseMatchingModel):
    def __init__(self) -> None:
        self.model_names = {
            "english": "all-MiniLM-L6-v2",
            "multilingual": "paraphrase-multilingual-mpnet-base-v2",
        }
        self.backends = {
            "english": self._build_backend(self.model_names["english"]),
            "multilingual": self._build_backend(self.model_names["multilingual"]),
        }
        self.cache: Dict[str, np.ndarray] = {}

    def _build_backend(self, model_name: str):
        if SentenceTransformer is None:
            return _LocalEmbeddingBackend()
        try:
            return _SentenceTransformerBackend(model_name)
        except Exception:
            return _LocalEmbeddingBackend()

    @staticmethod
    def _cache_key(text: str, backend_key: str) -> str:
        return f"{backend_key}:{hashlib.md5((text or '').encode('utf-8')).hexdigest()}"

    def _encode_text(self, text: str, backend_key: str) -> np.ndarray:
        cache_key = self._cache_key(text, backend_key)
        if cache_key not in self.cache:
            self.cache[cache_key] = self.backends[backend_key].encode([text or ""])[0]
        return self.cache[cache_key]

    def _similarity(self, text_a: str, text_b: str, backend_key: str) -> float:
        vector_a = self._encode_text(text_a, backend_key).reshape(1, -1)
        vector_b = self._encode_text(text_b, backend_key).reshape(1, -1)
        return float(np.clip(cosine_similarity(vector_a, vector_b)[0, 0], 0.0, 1.0))

    def section_aware_similarity(self, cv_sections, job_text: str) -> float:
        weights = {
            "experience": 0.45,
            "skills": 0.25,
            "summary": 0.15,
            "education": 0.10,
            "languages": 0.05,
        }
        weighted_scores = []
        for section, weight in weights.items():
            content = cv_sections.get(section, "")
            if not content:
                continue
            section_score = 0.5 * self._similarity(content, job_text, "english") + 0.5 * self._similarity(content, job_text, "multilingual")
            weighted_scores.append(weight * section_score)
        return float(np.clip(sum(weighted_scores), 0.0, 1.0))

    def predict(self, cv: str, job: str) -> float:
        base_score = 0.5 * self._similarity(cv, job, "english") + 0.5 * self._similarity(cv, job, "multilingual")
        section_score = self.section_aware_similarity(segment_cv(cv), job)
        return float(np.clip(0.7 * base_score + 0.3 * section_score, 0.0, 1.0))

    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[float]:
        cv_list = list(cvs)
        job_list = list(jobs)
        if len(cv_list) != len(job_list):
            raise ValueError("CV and job lists must have the same length.")
        return [self.predict(cv, job) for cv, job in zip(cv_list, job_list)]

