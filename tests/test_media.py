```python
import pytest
from fastapi.testclient import TestClient
from app.models import User, Media, Jobsite
from app.core.security import get_password_hash
import io

@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("Test123!@#"),
        is_verified=True,
        company_name="Test Company",
        values="Quality, Service",
        specialties="Remodeling"
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def test_jobsite(db, test_user):
    jobsite = Jobsite(
        address="123 Test St",
        user_id=test_user.id
    )
    db.add(jobsite)
    db.commit()
    return jobsite

def test_upload_media(client, test_user, test_jobsite):
    # Create test file
    file_content = b"test image content"
    files = {
        "file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")
    }
    data = {
        "jobsite_address": test_jobsite.address,
        "description": "Test media",
        "notes": "Test notes",
        "star_rating": 5,
        "earliest_upload": "ASAP",
        "status": "before"
    }

    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"}
    )
    token = response.json()["access_token"]

    # Upload media
    response = client.post(
        "/api/media/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "media_id" in data
    assert "file_url" in data

def test_list_media(client, db, test_user):
    # Add test media
    media = Media(
        file_url="test.jpg",
        description="Test media",
        star_rating=5,
        status="before",
        user_id=test_user.id,
        jobsite_id=1
    )
    db.add(media)
    db.commit()

    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"}
    )
    token = response.json()["access_token"]

    # List media
    response = client.get(
        "/api/media",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Test media"
```