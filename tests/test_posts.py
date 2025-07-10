```python
import pytest
from datetime import datetime, timedelta
from app.models import User, Post, MediaGrouping, Jobsite
from app.core.security import get_password_hash

@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("Test123!@#"),
        is_verified=True
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

@pytest.fixture
def test_grouping(db, test_jobsite):
    grouping = MediaGrouping(
        jobsite_id=test_jobsite.id,
        generated_caption="Test caption"
    )
    db.add(grouping)
    db.commit()
    return grouping

def test_create_post(client, db, test_user, test_jobsite, test_grouping):
    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"}
    )
    token = response.json()["access_token"]

    # Create post
    post_data = {
        "grouping_id": test_grouping.id,
        "caption": "Test post",
        "scheduled_for": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "platforms": ["instagram", "facebook"]
    }
    response = client.post(
        "/api/posts",
        json=post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "scheduled"

def test_get_unpublished_posts(client, db, test_user, test_jobsite, test_grouping):
    # Create test post
    post = Post(
        user_id=test_user.id,
        jobsite_id=test_jobsite.id,
        grouping_id=test_grouping.id,
        status="not_scheduled"
    )
    db.add(post)
    db.commit()

    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Test123!@#"}
    )
    token = response.json()["access_token"]

    # Get unpublished posts
    response = client.get(
        "/api/posts/unpublished",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "not_scheduled"
```