from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from src.api.main import app


pytestmark = pytest.mark.skipif(app is None, reason="FastAPI is not installed in this environment.")


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_match_endpoint():
    client = TestClient(app)
    payload = {
        "cv_text": "Python ML engineer with mlflow docker and communication",
        "job_text": "Required python, mlflow, docker. Soft skills: communication.",
        "model": "hybrid",
    }
    response = client.post("/api/v1/match", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "score" in body
    assert "explanation" in body
