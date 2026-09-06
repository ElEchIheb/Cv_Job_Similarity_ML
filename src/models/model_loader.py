from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger("jobtest.model_loader")

# Try to import models required for deserialization
try:
    from src.fusion.hybrid_scorer import HybridMatcher
    from src.models.embedding_model import EmbeddingMatcher
    from src.models.skill_matcher import SkillMatcher
    from src.models.tfidf_model import TFIDFMatcher
    from src.explainability.explainer import MatchingExplainer, RecommendationEngine
except ImportError:
    pass


def load_production_models() -> Dict:
    """
    Unified production model loader.
    Loads the trained HybridMatcher checkpoint, fails loudly if missing or invalid,
    and returns all required services for the platform.
    """
    logger.info("Initializing production AI services from checkpoint...")
    
    project_root = Path(__file__).resolve().parents[2]
    checkpoint_path = project_root / "models" / "checkpoints" / "hybrid.pkl"
    
    if not checkpoint_path.exists():
        raise RuntimeError(
            f"Production Hybrid checkpoint not found at {checkpoint_path}. "
            "Train and export the model using `python scripts/export_production_model.py` before starting inference."
        )
        
    try:
        with open(checkpoint_path, "rb") as f:
            hybrid = pickle.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load production checkpoint: {e}") from e
        
    # Validation
    if not hasattr(hybrid, "models") or "tfidf" not in hybrid.models:
        raise RuntimeError("Invalid checkpoint: missing 'tfidf' in HybridMatcher.models")
        
    tfidf = hybrid.models["tfidf"]
    if not getattr(tfidf, "is_fitted", False):
        raise RuntimeError("Invalid checkpoint: TFIDFMatcher is not fitted in the loaded production model.")
        
    logger.info("Production checkpoint validated successfully.")
    
    # Re-inject models stripped during checkpointing
    if "embedding" not in hybrid.models:
        hybrid.models["embedding"] = EmbeddingMatcher()
    if "skill" not in hybrid.models:
        hybrid.models["skill"] = SkillMatcher()
    
    # Construct the services dictionary
    services = {
        "hybrid":      hybrid,
        "embedding":   hybrid.models["embedding"],
        "skill":       hybrid.models["skill"],
        "tfidf":       tfidf,
        "explainer":   MatchingExplainer(),
        "recommender": RecommendationEngine(),
    }
    
    logger.info("All production AI services ready.")
    return services
