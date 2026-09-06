from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Dict, Iterable, List

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher


@dataclass
class FoldMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float


class HybridMatcher:
    def __init__(self, weights: Dict[str, float] | None = None) -> None:
        self.models: Dict[str, object] = {
            "tfidf": TFIDFMatcher(),
            "embedding": EmbeddingMatcher(),
            "skill": SkillMatcher(),
        }
        self.weights = self._normalize_weights(weights) if weights else {"tfidf": 0.2, "embedding": 0.4, "skill": 0.4}
        self.optimal_threshold = 0.60
        
    def _calculate_confidence(self, score: float) -> str:
        import math
        # Calibrate distance to a [0, 1] scale using a scaled sigmoid
        # This is a Score Confidence, NOT a calibrated probability.
        prob = 1.0 / (1.0 + math.exp(-10 * (score - getattr(self, "optimal_threshold", 0.60))))
        if prob >= 0.85 or prob <= 0.15: return "high"
        if prob >= 0.65 or prob <= 0.35: return "medium"
        return "low"

    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(max(value, 0.0) for value in weights.values()) or 1.0
        return {key: round(max(value, 0.0) / total, 4) for key, value in weights.items()}

    def fit(self, train_df) -> "HybridMatcher":
        self.models["tfidf"].fit_pairs(train_df["cv_text"].tolist(), train_df["job_text"].tolist())
        return self

    def predict(self, cv: str, job: str) -> Dict[str, object]:
        tfidf_score = self.models["tfidf"].predict(cv, job)
        embedding_score = self.models["embedding"].predict(cv, job)
        skill_details = self.models["skill"].predict_detailed(cv, job)
        skill_score = float(skill_details["score"])

        scores = {
            "tfidf_score": tfidf_score,
            "embedding_score": embedding_score,
            "skill_score": skill_score,
        }
        final_score = sum(self.weights[key.replace("_score", "")] * value for key, value in scores.items())
        final_score = float(np.clip(final_score, 0.0, 1.0))
        return {
            "final_score": round(final_score, 4),
            "percentage": round(final_score * 100.0, 1),
            "label": 1 if final_score >= getattr(self, "optimal_threshold", 0.60) else 0,
            "confidence": self._calculate_confidence(final_score),
            "component_scores": {key: round(value, 4) for key, value in scores.items()},
            "weights_used": dict(self.weights),
            "skill_details": skill_details,
        }

    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[Dict[str, object]]:
        return [self.predict(cv, job) for cv, job in zip(cvs, jobs)]

    def _compute_component_scores(self, df) -> Dict[str, np.ndarray]:
        tfidf = np.asarray(self.models["tfidf"].batch_predict(df["cv_text"].tolist(), df["job_text"].tolist()))
        embedding = np.asarray(self.models["embedding"].batch_predict(df["cv_text"].tolist(), df["job_text"].tolist()))
        skill = np.asarray(self.models["skill"].batch_predict(df["cv_text"].tolist(), df["job_text"].tolist()))
        return {"tfidf": tfidf, "embedding": embedding, "skill": skill}

    def _score_with_weights(self, components: Dict[str, np.ndarray], weights: Dict[str, float]) -> np.ndarray:
        return (
            weights["tfidf"] * components["tfidf"]
            + weights["embedding"] * components["embedding"]
            + weights["skill"] * components["skill"]
        )

    @staticmethod
    def _metric_bundle(y_true: np.ndarray, y_scores: np.ndarray, threshold: float = 0.60) -> Dict[str, float]:
        y_pred = (y_scores >= threshold).astype(int)
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        }
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.0
        return metrics

    def optimize_weights(self, train_df, validation_df=None, step: float = 0.1) -> Dict[str, object]:
        if validation_df is None:
            stratify = train_df["label"].astype(str) + "_" + train_df["domain"].astype(str)
            train_df, validation_df = train_test_split(
                train_df,
                test_size=0.2,
                random_state=42,
                stratify=stratify,
            )

        self.fit(train_df)
        validation_components = self._compute_component_scores(validation_df)
        y_true = validation_df["label"].astype(int).to_numpy()

        candidate_weights: List[Dict[str, float]] = []
        grid = np.arange(0.0, 1.0 + step, step)
        for embedding_weight in grid:
            for skill_weight in grid:
                tfidf_weight = round(1.0 - embedding_weight - skill_weight, 10)
                if tfidf_weight < 0.0:
                    continue
                candidate_weights.append(
                    self._normalize_weights(
                        {
                            "embedding": float(embedding_weight),
                            "skill": float(skill_weight),
                            "tfidf": float(tfidf_weight),
                        }
                    )
                )

        best_weights = self.weights
        best_auc = -1.0
        
        # Optimize weights purely on AUC (threshold independent)
        for weights in candidate_weights:
            scores = self._score_with_weights(validation_components, weights)
            auc = float(roc_auc_score(y_true, scores)) if len(set(y_true)) > 1 else 0.0
            if auc > best_auc:
                best_weights = weights
                best_auc = auc

        self.weights = best_weights
        
        # Find optimal classification threshold for best weights using F1
        best_scores = self._score_with_weights(validation_components, best_weights)
        best_threshold = 0.60
        best_f1 = -1.0
        
        min_score = float(np.min(best_scores))
        max_score = float(np.max(best_scores))
        if max_score <= min_score + 0.02:
            min_score = max(0.0, min_score - 0.05)
            max_score = min(1.0, max_score + 0.05)
            
        search_grid = np.arange(min_score, max_score + 0.02, 0.02)
        
        for thresh in search_grid:
            metrics = self._metric_bundle(y_true, best_scores, threshold=thresh)
            if metrics["f1"] > best_f1:
                best_f1 = metrics["f1"]
                best_threshold = thresh
                
        self.optimal_threshold = round(float(best_threshold), 4)
        best_metrics = self._metric_bundle(y_true, best_scores, threshold=self.optimal_threshold)

        return {
            "best_weights": best_weights,
            "optimal_threshold": self.optimal_threshold,
            "validation_metrics": best_metrics,
            "train_size": int(len(train_df)),
            "validation_size": int(len(validation_df)),
        }

    def cross_validate(self, df, k: int = 5, step: float = 0.1) -> Dict[str, object]:
        stratify = (df["label"].astype(str) + "_" + df["domain"].astype(str)).to_numpy()
        splitter = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        fold_metrics: List[FoldMetrics] = []

        for train_index, test_index in splitter.split(df, stratify):
            train_df = df.iloc[train_index].reset_index(drop=True)
            test_df = df.iloc[test_index].reset_index(drop=True)
            matcher = HybridMatcher(weights=dict(self.weights))
            matcher.models["embedding"] = self.models["embedding"]
            matcher.models["skill"] = self.models["skill"]
            matcher.optimize_weights(train_df, step=step)
            matcher.fit(train_df)
            components = matcher._compute_component_scores(test_df)
            y_true = test_df["label"].astype(int).to_numpy()
            y_scores = matcher._score_with_weights(components, matcher.weights)
            metrics = matcher._metric_bundle(y_true, y_scores, threshold=matcher.optimal_threshold)
            fold_metrics.append(FoldMetrics(**metrics))

        summary = {
            "accuracy_mean": mean(item.accuracy for item in fold_metrics),
            "accuracy_std": pstdev(item.accuracy for item in fold_metrics),
            "precision_mean": mean(item.precision for item in fold_metrics),
            "precision_std": pstdev(item.precision for item in fold_metrics),
            "recall_mean": mean(item.recall for item in fold_metrics),
            "recall_std": pstdev(item.recall for item in fold_metrics),
            "f1_mean": mean(item.f1 for item in fold_metrics),
            "f1_std": pstdev(item.f1 for item in fold_metrics),
            "roc_auc_mean": mean(item.roc_auc for item in fold_metrics),
            "roc_auc_std": pstdev(item.roc_auc for item in fold_metrics),
        }
        return {
            "folds": [item.__dict__ for item in fold_metrics],
            "summary": {key: round(value, 4) for key, value in summary.items()},
        }
