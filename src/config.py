"""
src/config.py
Centralised configuration for JobTest AI Platform.
Values are read from environment variables (with .env support).
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # pragma: no cover
    pass  # python-dotenv not installed — use raw os.environ

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings resolved at import time from environment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # API security
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.environ.get(
            "ALLOWED_ORIGINS", "http://localhost:8501,http://localhost:3000,http://localhost:3001,http://localhost:3002"
        ).split(",")
        if origin.strip()
    ]

    # Rate limiting
    REQUEST_LIMIT_PER_MINUTE: int = int(os.environ.get("REQUEST_LIMIT_PER_MINUTE", "60"))

    # Security & JWT
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # AI models
    EMBEDDING_MODEL_EN: str = os.environ.get("EMBEDDING_MODEL_EN", "all-mpnet-base-v2")
    EMBEDDING_MODEL_ML: str = os.environ.get(
        "EMBEDDING_MODEL_ML", "paraphrase-multilingual-mpnet-base-v2"
    )

    # Scoring
    MATCH_THRESHOLD: float = float(os.environ.get("MATCH_THRESHOLD", "0.60"))

    # ── LLM reasoning layer (Layer 2 — additive, optional) ────────────────────
    # A local Ollama runtime powers the qualitative "deep analysis". It is fully
    # optional: if Ollama is unreachable the core statistical evaluation is
    # completely unaffected and the deep-analysis section degrades gracefully.
    LLM_ENABLED: bool = os.environ.get("LLM_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    # Verified on the project's 8 GB, CPU-only machine with <2 GB free RAM.
    # Override with a larger model on capable machines.
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
    # Local CPU inference is slow — generous timeouts, but bounded.
    OLLAMA_TIMEOUT: float = float(os.environ.get("OLLAMA_TIMEOUT", "120"))
    OLLAMA_CONNECT_TIMEOUT: float = float(os.environ.get("OLLAMA_CONNECT_TIMEOUT", "3"))

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    DATA_DIR: Path = PROJECT_ROOT / "data"
    SKILLS_DICT_PATH: Path = DATA_DIR / "datasets" / "skills_dictionary.json"
    EVALUATION_DIR: Path = PROJECT_ROOT / "evaluation"
    
    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR.as_posix()}/neuralhire.db")


settings = Settings()
