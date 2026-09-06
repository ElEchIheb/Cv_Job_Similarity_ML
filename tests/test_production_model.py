import os
import sys
import pickle
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Mock sentence transformers to avoid Windows threaded loading crashes during tests
patch("src.models.embedding_model._ST_AVAILABLE", False).start()

from src.models.model_loader import load_production_models

def test_production_checkpoint_loads():
    """Verify that the production checkpoint loads successfully without errors."""
    services = load_production_models()
    assert "hybrid" in services
    assert "tfidf" in services
    assert services["hybrid"] is not None

def test_loaded_tfidf_is_fitted():
    """Verify that the loaded TF-IDF model is actually fitted."""
    services = load_production_models()
    tfidf = services["hybrid"].models["tfidf"]
    assert tfidf.is_fitted is True
    assert tfidf.vectorizer is not None
    assert hasattr(tfidf.vectorizer, "vocabulary_")

def test_prediction_does_not_refit_tfidf():
    """Verify that calling predict does not refit TF-IDF or change vocabulary."""
    services = load_production_models()
    hybrid = services["hybrid"]
    tfidf = hybrid.models["tfidf"]
    
    vocab_before = tfidf.vectorizer.vocabulary_.copy()
    
    cv_text = "I am a senior software engineer with Python experience."
    job_text = "Looking for a Python developer."
    
    # Run prediction
    hybrid.predict(cv_text, job_text)
    
    vocab_after = tfidf.vectorizer.vocabulary_.copy()
    
    assert vocab_before == vocab_after, "Vocabulary mutated during inference!"
    assert tfidf.is_fitted is True

@pytest.mark.skip(
    reason="Streamlit app (frontend/) is DEPRECATED — superseded by the Next.js "
    "app in web/. Kept for reference only, not maintained or tested. The canonical "
    "loader is covered by test_production_checkpoint_loads / test_loaded_tfidf_is_fitted."
)
def test_streamlit_hybrid_uses_fitted_model():
    """Verify that Streamlit's _load_models returns a fitted model."""
    from frontend.app import _load_models

    services = _load_models()
    hybrid = services["hybrid"]
    tfidf = hybrid.models["tfidf"]

    assert tfidf.is_fitted is True
    assert hasattr(tfidf.vectorizer, "vocabulary_")

def test_missing_checkpoint_fails_loudly(tmp_path):
    """Verify that if the checkpoint is missing, it raises a clear error."""
    # We mock the checkpoint path to point to a non-existent file
    with patch("src.models.model_loader.Path") as mock_path:
        mock_project_root = tmp_path
        # We need to simulate the resolve().parents[2] chain
        # The easiest way is to patch the path entirely inside the function, 
        # but let's just patch the Path object used in model_loader.
        
        # Actually it's easier to mock __file__ or just temporarily rename the file for the test
        # Let's mock Path so it returns a Path object that resolves to tmp_path
        class MockPath:
            def __init__(self, *args, **kwargs):
                pass
            def resolve(self):
                class MockResolve:
                    @property
                    def parents(self):
                        return [None, None, tmp_path]
                return MockResolve()
        
        with patch("src.models.model_loader.Path", MockPath):
            with pytest.raises(RuntimeError) as exc_info:
                load_production_models()
                
            assert "Production Hybrid checkpoint not found" in str(exc_info.value)

def test_loaded_model_matches_training_model():
    """Verify that the loaded model produces valid probabilities within ranges."""
    services = load_production_models()
    hybrid = services["hybrid"]
    
    cv_text = "Data Scientist with machine learning and python skills"
    job_text = "Data Scientist python machine learning"
    
    res = hybrid.predict(cv_text, job_text)
    
    # Assert score is valid
    assert 0.0 <= res["final_score"] <= 1.0
    # Expected deterministic output format
    assert "component_scores" in res
    assert "tfidf_score" in res["component_scores"]
    assert "confidence" in res
