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
from src.fusion.hybrid_scorer import HybridMatcher
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
    
    logger.info("Setting mathematically validated weights and threshold...")
    
    # Bypass HybridMatcher.__init__ to prevent EmbeddingMatcher from loading 
    # heavy HuggingFace models, which cause native C++ thread crashes on Windows during GC/pickle.
    from src.models.tfidf_model import TFIDFMatcher
    hybrid = HybridMatcher.__new__(HybridMatcher)
    hybrid.models = {"tfidf": TFIDFMatcher()}
    hybrid.weights = {"tfidf": 0.9, "embedding": 0.0, "skill": 0.1}
    hybrid.optimal_threshold = 0.04
    
    logger.info(f"Using weights: {hybrid.weights}")
    logger.info(f"Using threshold: {hybrid.optimal_threshold}")
    
    logger.info("Fitting TFIDFMatcher on Training & Validation data...")
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
