import os
import sys
from pathlib import Path
import json
import pickle
import pandas as pd
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.evaluator import EvaluationSuite
from src.fusion.hybrid_scorer import DOCUMENTED_DEFAULT_WEIGHTS, HybridMatcher
from src.models.tfidf_model import TFIDFMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("export_model")

def export_model():
    dataset_path = PROJECT_ROOT / "data" / "datasets" / "cv_job_dataset.csv"
    if not dataset_path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        sys.exit(1)
        
    logger.info("Loading dataset...")
    df = pd.read_csv(dataset_path)
    
    logger.info("Applying stratified splits exactly as in evaluation...")
    suite = EvaluationSuite()
    split = suite.stratified_split(df)
    
    logger.info(f"Split sizes: Train={len(split.train)}, Validation={len(split.validation)}, Test={len(split.test)}")
    
    # The fusion weights and the score calibration are produced together by
    # evaluation/calibration_study.py (selection on train/validation only).
    calibration_path = PROJECT_ROOT / "models" / "checkpoints" / "score_calibration.json"
    weights = dict(DOCUMENTED_DEFAULT_WEIGHTS)
    if calibration_path.exists():
        weights = json.loads(calibration_path.read_text(encoding="utf-8"))["provenance"]["hybrid_weights"]
    logger.info("Using fusion weights: %s", weights)
    hybrid = HybridMatcher(weights=weights)

    # The calibration anchors were learned on TF-IDF scores from a vectorizer
    # fitted on the TRAINING split only; the deployable checkpoint must use the
    # same vectorizer, otherwise the learned cut points would not apply exactly.
    hybrid.fit(split.train)
    # The experimental binary threshold is a benchmark artefact (not used for
    # decisions); keep the recorded value instead of re-scoring validation.
    results_path = PROJECT_ROOT / "evaluation" / "results" / "evaluation_results.json"
    if results_path.exists():
        hybrid.optimal_threshold = json.loads(results_path.read_text(encoding="utf-8"))[
            "metrics"]["hybrid"]["operating_threshold"]
    logger.info("Experimental threshold kept for reference only: %s", hybrid.optimal_threshold)

    logger.info(f"TFIDF is_fitted status: {hybrid.models['tfidf'].is_fitted}")
    
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "hybrid.pkl"
    
    logger.info(f"Exporting model to {checkpoint_path}...")
    
    # Strip heavy / unpicklable models before dumping (they are stateless and get re-initialized on load)
    if "embedding" in hybrid.models:
        del hybrid.models["embedding"]
    if "skill" in hybrid.models:
        del hybrid.models["skill"]
        
    with open(checkpoint_path, "wb") as f:
        pickle.dump(hybrid, f)
        
    logger.info("Production model exported successfully.")

if __name__ == "__main__":
    export_model()
