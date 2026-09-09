import os
import sys
from pathlib import Path
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
    
    logger.info("Using the documented production fusion weights (no weight optimization)...")
    hybrid = HybridMatcher(weights=DOCUMENTED_DEFAULT_WEIGHTS)
    hybrid.fit(split.train)
    calibration = hybrid.calibrate_threshold(split.validation)
    logger.info("Using weights: %s", hybrid.weights)
    logger.info("Validation-calibrated threshold: %s", hybrid.optimal_threshold)

    # The validation split selects only the operating threshold. Refit the
    # vocabulary on train+validation for the deployable checkpoint; test is
    # never read by this export path.
    logger.info("Refitting TFIDFMatcher on Training & Validation data...")
    hybrid.fit(pd.concat([split.train, split.validation], ignore_index=True))
    
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
