from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.evaluator import EvaluationSuite
from src.explainability.explainer import MatchingExplainer, RecommendationEngine
from src.fusion.hybrid_scorer import HybridMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher


st.set_page_config(page_title="CV Matching Dashboard", layout="wide")

HYBRID = HybridMatcher()
EXPLAINER = MatchingExplainer()
RECOMMENDER = RecommendationEngine()
MODELS = {
    "tfidf": TFIDFMatcher(),
    "embedding": EmbeddingMatcher(),
    "skill": SkillMatcher(),
    "hybrid": HYBRID,
}


def draw_gauge(score_percentage: float):
    figure, axis = plt.subplots(figsize=(4, 2.6), subplot_kw={"projection": "polar"})
    axis.set_theta_zero_location("W")
    axis.set_theta_direction(-1)
    axis.set_ylim(0, 1)
    axis.barh(0.5, width=3.14, left=0, height=0.35, color="#e9ecef")
    angle = 3.14 * min(max(score_percentage / 100.0, 0.0), 1.0)
    axis.barh(0.5, width=angle, left=0, height=0.35, color="#2a9d8f")
    axis.set_axis_off()
    st.pyplot(figure, clear_figure=True)


def draw_radar(radar_data: Dict[str, List[float]]):
    labels = radar_data["labels"]
    values = radar_data["cv_scores"] + [radar_data["cv_scores"][0]]
    requirements = radar_data["job_requirements"] + [radar_data["job_requirements"][0]]
    angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
    angles += angles[:1]

    figure, axis = plt.subplots(figsize=(5, 5), subplot_kw={"projection": "polar"})
    axis.plot(angles, values, linewidth=2, label="CV")
    axis.fill(angles, values, alpha=0.20)
    axis.plot(angles, requirements, linewidth=2, label="Offre")
    axis.set_xticks(angles[:-1])
    axis.set_xticklabels(labels)
    axis.set_yticklabels([])
    axis.legend(loc="upper right")
    st.pyplot(figure, clear_figure=True)


def run_match(cv_text: str, job_text: str, model: str = "hybrid") -> Dict[str, object]:
    if model == "hybrid":
        result = HYBRID.predict(cv_text, job_text)
    else:
        score = float(MODELS[model].predict(cv_text, job_text))
        result = {
            "final_score": score,
            "percentage": round(score * 100.0, 1),
            "label": 1 if score >= 0.60 else 0,
            "component_scores": {f"{model}_score": round(score, 4)},
            "skill_details": MODELS["skill"].predict_detailed(cv_text, job_text),
        }
    explanation = EXPLAINER.explain(cv_text, job_text, result)
    recommendations = RECOMMENDER.generate(explanation["gap_analysis"])
    return {"result": result, "explanation": explanation, "recommendations": recommendations}


page = st.sidebar.radio(
    "Pages",
    ["Matching individuel", "Comparaison modeles", "Analyse batch", "Dashboard evaluation"],
)

st.title("Systeme hybride de matching CV / offre")

if page == "Matching individuel":
    cv_text = st.text_area("CV", height=240, value="PROFIL\nML Engineer avec 5 ans d'experience en python, mlflow, docker, kubernetes.\nCOMPETENCES\npython, mlflow, kubernetes, pytorch, fastapi, communication")
    job_text = st.text_area("Offre", height=240, value="Nous cherchons un ML Engineer. Competences obligatoires: python, mlflow, kubernetes, docker, model serving. Soft skills: communication, collaboration.")
    if st.button("Calculer le matching"):
        payload = run_match(cv_text, job_text, model="hybrid")
        result = payload["result"]
        explanation = payload["explanation"]
        recommendations = payload["recommendations"]

        left, right = st.columns(2)
        with left:
            st.metric("Score global", f"{result['percentage']}%")
            draw_gauge(result["percentage"])
        with right:
            draw_radar(explanation["radar_data"])

        st.subheader("Analyse")
        st.json(explanation)
        st.subheader("Recommandations")
        st.json(recommendations)

elif page == "Comparaison modeles":
    cv_text = st.text_area("CV compare", height=200)
    job_text = st.text_area("Offre compare", height=200)
    if st.button("Comparer"):
        rows = []
        for model_name in ["tfidf", "embedding", "skill", "hybrid"]:
            payload = run_match(cv_text, job_text, model=model_name)
            rows.append(
                {
                    "modele": model_name,
                    "score": payload["result"]["final_score"],
                    "pourcentage": payload["result"]["percentage"],
                    "label": payload["result"]["label"],
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

elif page == "Analyse batch":
    uploaded = st.file_uploader("Uploader un CSV avec les colonnes cv_text et job_text", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        if {"cv_text", "job_text"}.issubset(df.columns):
            rows = []
            for _, row in df.iterrows():
                payload = run_match(str(row["cv_text"]), str(row["job_text"]), model="hybrid")
                rows.append({"score": payload["result"]["final_score"], "percentage": payload["result"]["percentage"], "label": payload["result"]["label"]})
            result_df = pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
            st.dataframe(result_df, use_container_width=True)
            st.download_button("Telecharger les resultats", result_df.to_csv(index=False).encode("utf-8"), file_name="batch_results.csv")
        else:
            st.error("Le fichier doit contenir les colonnes cv_text et job_text.")

else:
    results_path = PROJECT_ROOT / "evaluation" / "results" / "evaluation_results.json"
    if results_path.exists():
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        st.subheader("Metriques")
        st.json(payload["metrics"])
        st.subheader("Analyse statistique")
        st.json(payload["analysis"])
        figures_dir = PROJECT_ROOT / "evaluation" / "figures"
        for figure_name in [
            "roc_curves.png",
            "confusion_matrices.png",
            "score_boxplot.png",
            "domain_score_heatmap.png",
            "f1_scores.png",
            "embedding_vs_skill.png",
        ]:
            figure_path = figures_dir / figure_name
            if figure_path.exists():
                st.image(str(figure_path), caption=figure_name)
    else:
        st.info("Aucun resultat d'evaluation trouve. Lancez d'abord le pipeline d'evaluation.")
        if st.button("Generer une evaluation de demonstration"):
            dataset_path = PROJECT_ROOT / "data" / "datasets" / "cv_job_dataset.csv"
            if dataset_path.exists():
                suite = EvaluationSuite()
                suite.run_full_evaluation(dataset_path)
                st.experimental_rerun()
            else:
                st.error("Dataset manquant. Generez d'abord le dataset.")
