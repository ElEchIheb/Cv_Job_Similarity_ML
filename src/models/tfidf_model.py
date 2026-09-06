from __future__ import annotations

from typing import Iterable, List

import numpy as np
from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base_model import BaseMatchingModel


class TFIDFMatcher(BaseMatchingModel):
    def __init__(self) -> None:
        self.vectorizer = self._build_vectorizer(min_df=2)
        self.is_fitted = False

    @staticmethod
    def _build_vectorizer(min_df: int = 2) -> TfidfVectorizer:
        return TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=10000,
            sublinear_tf=True,
            min_df=min_df,
        )

    def fit(self, texts: Iterable[str]) -> "TFIDFMatcher":
        texts = [text or "" for text in texts]
        min_df = 2 if len(texts) >= 4 else 1
        self.vectorizer = self._build_vectorizer(min_df=min_df)
        try:
            self.vectorizer.fit(texts)
        except ValueError:
            self.vectorizer = self._build_vectorizer(min_df=1)
            self.vectorizer.fit(texts)
        self.is_fitted = True
        return self

    def fit_pairs(self, cvs: Iterable[str], jobs: Iterable[str]) -> "TFIDFMatcher":
        return self.fit(list(cvs) + list(jobs))

    def _ensure_fitted_for_inputs(self) -> None:
        if not self.is_fitted:
            raise RuntimeError("TFIDFMatcher is not fitted. Fit the model using training data before inference.")

    def predict(self, cv: str, job: str) -> float:
        self._ensure_fitted_for_inputs()
        matrix = self.vectorizer.transform([cv or "", job or ""])
        score = cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]
        return float(np.clip(score, 0.0, 1.0))

    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[float]:
        cv_list = list(cvs)
        job_list = list(jobs)
        if len(cv_list) != len(job_list):
            raise ValueError("CV and job lists must have the same length.")
        self._ensure_fitted_for_inputs()
        cv_matrix = self.vectorizer.transform([text or "" for text in cv_list])
        job_matrix = self.vectorizer.transform([text or "" for text in job_list])
        scores = cosine_similarity(cv_matrix, job_matrix).diagonal()
        return [float(np.clip(score, 0.0, 1.0)) for score in scores]

    def save(self, file_path: str) -> None:
        payload = {"vectorizer": self.vectorizer, "is_fitted": self.is_fitted}
        dump(payload, file_path)

    def load(self, file_path: str) -> "TFIDFMatcher":
        payload = load(file_path)
        self.vectorizer = payload["vectorizer"]
        self.is_fitted = payload["is_fitted"]
        return self

