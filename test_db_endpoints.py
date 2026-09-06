from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_db():
    print("Testing Candidate creation...")
    resp = client.post("/api/v1/candidates", json={
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890"
    })
    print("Response Status:", resp.status_code)
    print("Response JSON:", resp.json())
    assert resp.status_code == 200
    
    print("\nTesting JobOffer creation...")
    resp = client.post("/api/v1/job-offers", json={
        "title": "Software Engineer",
        "description": "We are looking for a Python developer with FastAPI experience.",
        "required_skills": "Python, FastAPI, SQL"
    })
    print("Response Status:", resp.status_code)
    print("Response JSON:", resp.json())
    assert resp.status_code == 200

if __name__ == "__main__":
    test_db()
    print("\nAll database tests passed!")
