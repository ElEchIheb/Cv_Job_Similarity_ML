from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List

from .parser import clean_text, segment_cv, tokenize_and_normalize


class TextPreprocessor:
    """Batch-oriented text preprocessor with memoized outputs."""

    def __init__(self) -> None:
        self.cache: Dict[str, Dict[str, object]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    @staticmethod
    def _make_cache_key(text: str) -> str:
        return hashlib.md5((text or "").encode("utf-8")).hexdigest()

    def transform(self, text: str) -> Dict[str, object]:
        cache_key = self._make_cache_key(text)
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]

        self.cache_misses += 1
        cleaned = clean_text(text)
        sections = segment_cv(text)
        payload: Dict[str, object] = {
            "raw_text": text,
            "clean_text": cleaned,
            "tokens": tokenize_and_normalize(cleaned),
            "sections": sections,
        }
        self.cache[cache_key] = payload
        return payload

    def fit_transform(self, texts: Iterable[str]) -> List[Dict[str, object]]:
        return [self.transform(text) for text in texts]

