"""
tests/conftest.py
Pytest configuration and shared fixtures for the JobTest AI Platform test suite.

Key fixture: mock_sentence_transformer (autouse=True, session-scoped)
  — Patches SentenceTransformer with a fast mock that returns normalised random
    vectors. This avoids real model loading during tests, which would crash
    under Python 3.13 + PyTorch due to a known threading incompatibility
    in PyTorch's C extension when called from within anyio's thread pool
    (used by FastAPI's TestClient).

  Tests validate: API routing, request/response structure, business logic,
                  Pydantic validation, PDF generation, and ranking logic.
  Embedding quality is validated separately via the evaluation suite.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Prevent HuggingFace tokenizer from spawning extra threads
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── SentenceTransformer mock ─────────────────────────────────────────────────

def _make_mock_st_model() -> MagicMock:
    """Build a lightweight SentenceTransformer mock.

    Returns normalised random vectors of the same dimensionality as
    all-MiniLM-L6-v2 (384) to allow cosine similarity to work correctly.
    """
    mock = MagicMock()

    def _encode(texts, normalize_embeddings: bool = True, show_progress_bar: bool = False, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        n = len(texts)
        rng = np.random.default_rng(seed=42)  # fixed seed = deterministic tests
        vecs = rng.standard_normal((n, 384)).astype(np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.maximum(norms, 1e-9)
        return vecs

    mock.encode.side_effect = _encode
    mock.get_sentence_embedding_dimension.return_value = 384
    return mock


@pytest.fixture(scope="session", autouse=True)
def mock_sentence_transformer():
    """Session-scoped autouse fixture: patch SentenceTransformer for all tests.

    This prevents real model downloads/loading and avoids the Python 3.13 +
    PyTorch threading crash (access violation in torch/storage.py when called
    from within anyio's thread pool under concurrent.futures.thread).
    """
    mock_model = _make_mock_st_model()

    # Patch at the module level where SentenceTransformer is imported
    with patch("sentence_transformers.SentenceTransformer", return_value=mock_model), \
         patch("src.models.embedding_model.SentenceTransformer", return_value=mock_model), \
         patch("src.models.tfidf_model.TFIDFMatcher._ensure_fitted_for_inputs", return_value=None):
        yield mock_model


# ── Shared heavy fixtures (session-scoped, built AFTER mock is active) ────────

@pytest.fixture(scope="session")
def hybrid_matcher(mock_sentence_transformer):
    """HybridMatcher — uses mocked SentenceTransformer, loads once per session."""
    from src.fusion.hybrid_scorer import HybridMatcher
    return HybridMatcher()


@pytest.fixture(scope="session")
def embedding_matcher(mock_sentence_transformer):
    """EmbeddingMatcher — uses mocked SentenceTransformer."""
    from src.models.embedding_model import EmbeddingMatcher
    return EmbeddingMatcher()
