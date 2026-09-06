import os
import sys
import json
from fastapi.testclient import TestClient

# Add project root to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set a test database
os.environ["DATABASE_URL"] = "sqlite:///./test_workflow.db"

# Remove the test db if it exists
if os.path.exists("test_workflow.db"):
    os.remove("test_workflow.db")

from src.api.main import app
from src.database import Base, engine

# Create the schema in the test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def run_tests():
    print("Testing Candidate creation...")
    c_resp = client.post("/api/v1/candidates", json={
        "full_name": "Alice Workflow",
        "email": "alice@workflow.com",
        "phone": "+9876543210"
    })
    assert c_resp.status_code == 200
    candidate = c_resp.json()
    print("Candidate created:", candidate)

    print("\nTesting JobOffer creation...")
    j_resp = client.post("/api/v1/job-offers", json={
        "title": "Backend Python Developer",
        "description": "Looking for a Python dev with FastAPI skills.",
        "required_skills": "Python, FastAPI, SQL"
    })
    assert j_resp.status_code == 200
    job = j_resp.json()
    print("Job offer created:", job)

    print("\nTesting Match workflow...")
    m_resp = client.post("/api/v1/match", json={
        "cv_text": "I am a backend Python developer with 5 years of FastAPI experience.",
        "job_text": job["description"],
        "candidate_id": candidate["id"],
        "job_offer_id": job["id"],
        "model": "hybrid"
    })
    assert m_resp.status_code == 200
    match_result = m_resp.json()
    print("Match Result (score):", match_result.get("score"))
    print("Match ID:", match_result.get("match_id"))
    
    assert "match_id" in match_result, "Match was not saved to DB"

    print("\nTesting Match History retrieval...")
    mh_resp = client.get("/api/v1/matches")
    assert mh_resp.status_code == 200
    matches = mh_resp.json()
    print(f"Found {len(matches)} match records.")
    assert len(matches) > 0

    print("\nTesting Match Detail retrieval...")
    md_resp = client.get(f"/api/v1/matches/{match_result['match_id']}")
    assert md_resp.status_code == 200
    match_detail = md_resp.json()
    print("Match Detail Decision:", match_detail["decision"])
    
    print("\nAll workflow tests passed!")

if __name__ == "__main__":
    run_tests()
