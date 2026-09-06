"""
frontend/pages/__init__.py
NeuralHire pages package.
"""
from . import dashboard
from . import single_match
from . import model_comparison
from . import evaluation_metrics
from . import settings

__all__ = [
    "dashboard",
    "single_match",
    "ranking",
    "model_comparison",
    "evaluation_metrics",
    "settings",
]
