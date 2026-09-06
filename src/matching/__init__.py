"""src/matching — canonical evaluation + persistence service."""
from .service import run_evaluation, persist_evaluation, evaluate_and_persist

__all__ = ["run_evaluation", "persist_evaluation", "evaluate_and_persist"]
