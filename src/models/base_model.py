from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class BaseMatchingModel(ABC):
    threshold: float = 0.60

    @abstractmethod
    def predict(self, cv: str, job: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[float]:
        raise NotImplementedError

    def evaluate(self, test_df) -> Dict[str, float]:
        y_true = test_df["label"].astype(int).tolist()
        y_scores = self.batch_predict(test_df["cv_text"].tolist(), test_df["job_text"].tolist())
        y_pred = [1 if score >= self.threshold else 0 for score in y_scores]
        metrics: Dict[str, float] = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "pr_auc": float(average_precision_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.0,
            "kappa": float(cohen_kappa_score(y_true, y_pred)) if len(set(y_true)) > 1 else 0.0,
        }
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.0
        metrics["confusion_matrix"] = confusion_matrix(y_true, y_pred).astype(int).tolist()
        metrics["score_mean"] = float(np.mean(y_scores)) if y_scores else 0.0
        return metrics

