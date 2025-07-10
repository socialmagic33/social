from fastapi.testclient import TestClient
import pytest
from app.core.security import get_password_hash

def test_register(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "Test123!@#"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "verification_token" in data

def test_login_unverified(client, db):
    # Create unverified user
    from app.models import User
    db.add(User(
        email="test@example.com",
        hashed_password=get_password_hash("Test123!@#"),
        is_verified=False
    ))
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Test123!@#"}
    )
    assert response.status_code == 403
    assert "Email not verified" in response.json()["detail"]

def test_login_verified(client, db):
    # Create verified user
    from app.models import User
    db.add(User(
        email="test@example.com",
        hashed_password=get_password_hash("Test123!@#"),
        is_verified=True
    ))
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Test123!@#"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"