import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.database import get_db, Base
from src.security.auth import get_password_hash
import src.models_db as models_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@company.com", "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@company.com"
    assert data["full_name"] == "Test User"
    assert "id" in data

def test_register_existing_user():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@company.com", "password": "password123", "full_name": "Test User"}
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@company.com", "password": "newpassword", "full_name": "Another Name"}
    )
    assert response.status_code == 400

def test_login_success():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@company.com", "password": "password123", "full_name": "Test User"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@company.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@company.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_read_users_me():
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@company.com", "password": "password123", "full_name": "Test User"}
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@company.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@company.com"

def test_protected_endpoints_require_auth():
    response = client.get("/api/v1/candidates")
    assert response.status_code == 401
