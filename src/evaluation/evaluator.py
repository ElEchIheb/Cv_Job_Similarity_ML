from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import chi2
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from src.fusion.hybrid_scorer import HybridMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher


def evaluate_model(model, test_df) -> Dict[str, object]:
    start = time.perf_counter()
    y_scores = np.asarray(model.batch_predict(test_df["cv_text"].tolist(), test_df["job_text"].tolist()))
    elapsed = (time.perf_counter() - start) * 1000.0 / max(1, len(test_df))
    y_true = test_df["label"].astype(int).to_numpy()
    y_pred = (y_scores >= 0.60).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.0,
        "pr_auc": float(average_precision_score(y_true, y_scores)) if len(set(y_true)) > 1 else 0.0,
        "kappa": float(cohen_kappa_score(y_true, y_pred)) if len(set(y_true)) > 1 else 0.0,
        "confusion_matrix": confusion_matrix(y_true, y_pred).astype(int).tolist(),
        "inference_ms_per_pair": round(float(elapsed), 3),
        "scores": y_scores.tolist(),
        "predictions": y_pred.tolist(),
    }


@dataclass
class DatasetSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


class EvaluationSuite:
    def __init__(self, output_dir: str | Path = "evaluation") -> None:
        self.output_dir = Path(output_dir)
        self.results_dir = self.output_dir / "results"
        self.figures_dir = self.output_dir / "figures"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stratified_split(df: pd.DataFrame, random_state: int = 42) -> DatasetSplit:
        stratify_key = df["label"].astype(str) + "_" + df["domain"].astype(str)
        train_df, temp_df = train_test_split(
            df,
            test_size=0.30,
            random_state=random_state,
            stratify=stratify_key,
        )
        temp_key = temp_df["label"].astype(str) + "_" + temp_df["domain"].astype(str)
        validation_df, test_df = train_test_split(
            temp_df,
            test_size=0.50,
            random_state=random_state,
            stratify=temp_key,
        )
        return DatasetSplit(
            train=train_df.reset_index(drop=True),
            validation=validation_df.reset_index(drop=True),
            test=test_df.reset_index(drop=True),
        )

    @staticmethod
    def bootstrap_confidence_interval(y_true: np.ndarray, y_scores: np.ndarray, metric: str, iterations: int = 1000, threshold: float = 0.60) -> Tuple[float, float]:
        rng = np.random.default_rng(42)
        samples = []
        while len(samples) < iterations:
            indices = rng.integers(0, len(y_true), len(y_true))
            sample_true = y_true[indices]
            if len(set(sample_true)) <= 1:
                continue
            sample_scores = y_scores[indices]
            sample_pred = (sample_scores >= threshold).astype(int)
            if metric == "f1":
                value = f1_score(sample_true, sample_pred, zero_division=0)
            elif metric == "accuracy":
                value = accuracy_score(sample_true, sample_pred)
            else:
                value = roc_auc_score(sample_true, sample_scores)
            samples.append(value)
        return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))

    @staticmethod
    def mcnemar_test(y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray) -> Dict[str, float]:
        a_correct = pred_a == y_true
        b_correct = pred_b == y_true
        b01 = int(np.sum(a_correct & ~b_correct))
        b10 = int(np.sum(~a_correct & b_correct))
        statistic = (abs(b01 - b10) - 1) ** 2 / max(1, (b01 + b10))
        p_value = float(chi2.sf(statistic, 1))
        return {"b01": b01, "b10": b10, "statistic": float(statistic), "p_value": p_value}

    @staticmethod
    def subgroup_analysis(df: pd.DataFrame, metrics_by_model: Dict[str, Dict[str, object]]) -> Dict[str, object]:
        seniority_metrics = {}
        for seniority in df["seniority"].unique():
            mask = df["seniority"] == seniority
            if mask.sum() < 2: continue
            
            group_true = df.loc[mask, "label"].astype(int).to_numpy()
            if len(set(group_true)) < 2: continue
            
            hybrid_scores = np.asarray(metrics_by_model["hybrid"]["scores"])[mask]
            auc = roc_auc_score(group_true, hybrid_scores)
            seniority_metrics[str(seniority)] = {"count": int(mask.sum()), "auc": float(auc)}
            
        domain_metrics = {}
        for domain in df["domain"].unique():
            mask = df["domain"] == domain
            if mask.sum() < 2: continue
            
            group_true = df.loc[mask, "label"].astype(int).to_numpy()
            if len(set(group_true)) < 2: continue
            
            hybrid_scores = np.asarray(metrics_by_model["hybrid"]["scores"])[mask]
            auc = roc_auc_score(group_true, hybrid_scores)
            domain_metrics[str(domain)] = {"count": int(mask.sum()), "auc": float(auc)}

        return {
            "seniority_performance": seniority_metrics,
            "domain_performance": domain_metrics,
            "models_evaluated": list(metrics_by_model.keys()),
        }

    def _plot_roc_curves(self, y_true: np.ndarray, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        plt.figure(figsize=(8, 6))
        for model_name, metrics in metrics_by_model.items():
            scores = np.asarray(metrics["scores"])
            if len(set(y_true)) < 2:
                continue
            fpr, tpr, _ = roc_curve(y_true, scores)
            plt.plot(fpr, tpr, label=f"{model_name} (AUC={metrics['roc_auc']:.2f})")
        plt.plot([0, 1], [0, 1], linestyle="--", color="grey")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curves")
        plt.legend()
        plt.tight_layout()
        plt.savefig(self.figures_dir / "roc_curves.png", dpi=200)
        plt.close()

    def _plot_confusion_matrices(self, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        model_names = list(metrics_by_model.keys())
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        for axis, model_name in zip(axes.flatten(), model_names):
            matrix = np.asarray(metrics_by_model[model_name]["confusion_matrix"])
            sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", ax=axis, cbar=False)
            axis.set_title(model_name)
            axis.set_xlabel("Predicted")
            axis.set_ylabel("Actual")
        plt.tight_layout()
        plt.savefig(self.figures_dir / "confusion_matrices.png", dpi=200)
        plt.close(fig)

    def _plot_score_boxplot(self, test_df: pd.DataFrame, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        records = []
        for model_name, metrics in metrics_by_model.items():
            for label, score in zip(test_df["label"].tolist(), metrics["scores"]):
                records.append({"model": model_name, "label": label, "score": score})
        plot_df = pd.DataFrame(records)
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=plot_df, x="model", y="score", hue="label")
        plt.title("Score distribution by label")
        plt.tight_layout()
        plt.savefig(self.figures_dir / "score_boxplot.png", dpi=200)
        plt.close()

    def _plot_score_correlation(self, test_df: pd.DataFrame, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        correlation_df = pd.DataFrame(
            {
                "domain": test_df["domain"].tolist(),
                "tfidf": metrics_by_model["tfidf"]["scores"],
                "embedding": metrics_by_model["embedding"]["scores"],
                "skill": metrics_by_model["skill"]["scores"],
                "hybrid": metrics_by_model["hybrid"]["scores"],
            }
        )
        domain_means = correlation_df.groupby("domain").mean(numeric_only=True)
        plt.figure(figsize=(10, 6))
        sns.heatmap(domain_means, annot=True, cmap="viridis")
        plt.title("Correlation heatmap by domain")
        plt.tight_layout()
        plt.savefig(self.figures_dir / "domain_score_heatmap.png", dpi=200)
        plt.close()

    def _plot_f1_bars(self, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        plt.figure(figsize=(8, 5))
        names = list(metrics_by_model.keys())
        values = [metrics_by_model[name]["f1"] for name in names]
        sns.barplot(x=names, y=values, hue=names, legend=False)
        plt.ylim(0, 1)
        plt.title("Comparative F1-score")
        plt.tight_layout()
        plt.savefig(self.figures_dir / "f1_scores.png", dpi=200)
        plt.close()

    def _plot_embedding_skill_scatter(self, metrics_by_model: Dict[str, Dict[str, object]]) -> None:
        plt.figure(figsize=(8, 6))
        plt.scatter(metrics_by_model["embedding"]["scores"], metrics_by_model["skill"]["scores"], alpha=0.7)
        plt.xlabel("Embedding score")
        plt.ylabel("Skill score")
        plt.title("Embedding score vs skill score")
        plt.tight_layout()
        plt.savefig(self.figures_dir / "embedding_vs_skill.png", dpi=200)
        plt.close()

    def _error_analysis(self, test_df: pd.DataFrame, metrics_by_model: Dict[str, Dict[str, object]]) -> Dict[str, object]:
        hybrid_scores = np.asarray(metrics_by_model["hybrid"]["scores"])
        # Fetch the optimal threshold applied to hybrid predictions
        optimal_threshold = metrics_by_model["hybrid"].get("optimal_threshold", 0.60)
        hybrid_pred = (hybrid_scores >= optimal_threshold).astype(int)
        
        y_true = test_df["label"].astype(int).to_numpy()
        fp_mask = (hybrid_pred == 1) & (y_true == 0)
        fn_mask = (hybrid_pred == 0) & (y_true == 1)
        
        false_positives = test_df[fp_mask]
        false_negatives = test_df[fn_mask]
        
        return {
            "fp_count": int(fp_mask.sum()),
            "fn_count": int(fn_mask.sum()),
            "dominant_fp_domain": str(false_positives["domain"].mode()[0]) if len(false_positives) > 0 else None,
            "dominant_fn_domain": str(false_negatives["domain"].mode()[0]) if len(false_negatives) > 0 else None,
            "false_positives_examples": false_positives[["id", "domain", "seniority", "match_reason"]].head(5).to_dict(orient="records"),
            "false_negatives_examples": false_negatives[["id", "domain", "seniority", "match_reason"]].head(5).to_dict(orient="records"),
        }

    def run_full_evaluation(self, dataset_path: str | Path) -> Dict[str, object]:
        df = pd.read_csv(dataset_path)
        split = self.stratified_split(df)

        tfidf = TFIDFMatcher().fit_pairs(split.train["cv_text"].tolist(), split.train["job_text"].tolist())
        embedding = EmbeddingMatcher()
        skill = SkillMatcher()
        hybrid = HybridMatcher()
        hybrid.optimize_weights(split.train, split.validation)
        hybrid.fit(pd.concat([split.train, split.validation], ignore_index=True))

        metrics_by_model = {
            "tfidf": evaluate_model(tfidf, split.test),
            "embedding": evaluate_model(embedding, split.test),
            "skill": evaluate_model(skill, split.test),
        }

        start = time.perf_counter()
        hybrid_scores_dicts = hybrid.batch_predict(split.test["cv_text"], split.test["job_text"])
        hybrid_scores = [d["final_score"] for d in hybrid_scores_dicts]
        hybrid_inference_ms = (time.perf_counter() - start) * 1000.0 / max(1, len(split.test))
        y_true = split.test["label"].astype(int).to_numpy()
        hybrid_scores_array = np.asarray(hybrid_scores)
        optimal_threshold = getattr(hybrid, "optimal_threshold", 0.60)
        hybrid_pred = (hybrid_scores_array >= optimal_threshold).astype(int)
        
        metrics_by_model["hybrid"] = {
            "optimal_threshold": optimal_threshold,
            "accuracy": float(accuracy_score(y_true, hybrid_pred)),
            "precision": float(precision_score(y_true, hybrid_pred, zero_division=0)),
            "recall": float(recall_score(y_true, hybrid_pred, zero_division=0)),
            "f1": float(f1_score(y_true, hybrid_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_true, hybrid_scores_array)) if len(set(y_true)) > 1 else 0.0,
            "pr_auc": float(average_precision_score(y_true, hybrid_scores_array)) if len(set(y_true)) > 1 else 0.0,
            "kappa": float(cohen_kappa_score(y_true, hybrid_pred)) if len(set(y_true)) > 1 else 0.0,
            "confusion_matrix": confusion_matrix(y_true, hybrid_pred).astype(int).tolist(),
            "inference_ms_per_pair": round(float(hybrid_inference_ms), 3),
            "scores": hybrid_scores_array.tolist(),
            "predictions": hybrid_pred.tolist(),
        }

        stats = {
            "bootstrap_ci": {
                model_name: {
                    "f1": self.bootstrap_confidence_interval(y_true, np.asarray(metrics["scores"]), "f1", threshold=metrics.get("optimal_threshold", 0.60)),
                    "accuracy": self.bootstrap_confidence_interval(y_true, np.asarray(metrics["scores"]), "accuracy", threshold=metrics.get("optimal_threshold", 0.60)),
                    "roc_auc": self.bootstrap_confidence_interval(y_true, np.asarray(metrics["scores"]), "roc_auc", threshold=metrics.get("optimal_threshold", 0.60)),
                }
                for model_name, metrics in metrics_by_model.items()
            },
            "mcnemar": {
                "hybrid_vs_embedding": self.mcnemar_test(
                    y_true,
                    np.asarray(metrics_by_model["hybrid"]["predictions"]),
                    np.asarray(metrics_by_model["embedding"]["predictions"]),
                ),
                "hybrid_vs_skill": self.mcnemar_test(
                    y_true,
                    np.asarray(metrics_by_model["hybrid"]["predictions"]),
                    np.asarray(metrics_by_model["skill"]["predictions"]),
                ),
            },
            "subgroup_analysis": self.subgroup_analysis(split.test, metrics_by_model),
            "weight_optimization": hybrid.weights,
            "cross_validation": hybrid.cross_validate(pd.concat([split.train, split.validation], ignore_index=True)),
            "error_analysis": self._error_analysis(split.test, metrics_by_model),
            "split_sizes": {"train": len(split.train), "validation": len(split.validation), "test": len(split.test)},
        }

        self._plot_roc_curves(y_true, metrics_by_model)
        self._plot_confusion_matrices(metrics_by_model)
        self._plot_score_boxplot(split.test, metrics_by_model)
        self._plot_score_correlation(split.test, metrics_by_model)
        self._plot_f1_bars(metrics_by_model)
        self._plot_embedding_skill_scatter(metrics_by_model)

        payload = {"metrics": metrics_by_model, "analysis": stats}
        result_file = self.results_dir / "evaluation_results.json"
        result_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
