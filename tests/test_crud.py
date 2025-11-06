"""Test CRUD operations"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from .conftest import User, UserCreate, UserRead, UserUpdate


@pytest.fixture
def app(get_db):
    """Create FastAPI app with AutoCRUD router"""
    from fastapi_autocrud_rishabh import AutoCRUDRouter
    
    app = FastAPI()
    
    user_router = AutoCRUDRouter(
        model=User,
        create_schema=UserCreate,
        read_schema=UserRead,
        update_schema=UserUpdate,
        db_session=get_db,
        prefix="/users",
        tags=["Users"]
    )
    
    app.include_router(user_router.router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


def test_create_user(client):
    """Test creating a new user"""
    response = client.post(
        "/users/",
        json={"name": "Test User", "email": "test@example.com", "age": 25}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["age"] == 25
    assert "id" in data


def test_create_user_duplicate_email(client):
    """Test creating user with duplicate email"""
    user_data = {"name": "Test User", "email": "test@example.com", "age": 25}
    
    # First creation should succeed
    response1 = client.post("/users/", json=user_data)
    assert response1.status_code == 201
    
    # Second creation should fail (duplicate email)
    response2 = client.post("/users/", json=user_data)
    assert response2.status_code == 500  # Database error


def test_list_users_empty(client):
    """Test listing users when database is empty"""
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0


def test_list_users(client, sample_users):
    """Test listing all users"""
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 5


def test_list_users_pagination(client, sample_users):
    """Test pagination"""
    # Get first 2 users
    response = client.get("/users/?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0
    
    # Get next 2 users
    response = client.get("/users/?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


def test_get_user_by_id(client, sample_users):
    """Test getting user by ID"""
    user_id = sample_users[0].id
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Alice"


def test_get_user_not_found(client):
    """Test getting non-existent user"""
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_user(client, sample_users):
    """Test updating user"""
    user_id = sample_users[0].id
    response = client.put(
        f"/users/{user_id}",
        json={"name": "Alice Updated", "age": 26}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice Updated"
    assert data["age"] == 26
    assert data["email"] == "alice@example.com"  # Unchanged


def test_update_user_not_found(client):
    """Test updating non-existent user"""
    response = client.put(
        "/users/999",
        json={"name": "Updated"}
    )
    assert response.status_code == 404


def test_delete_user(client, sample_users):
    """Test deleting user"""
    user_id = sample_users[0].id
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Item deleted successfully"
    
    # Verify user is deleted
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404


def test_delete_user_not_found(client):
    """Test deleting non-existent user"""
    response = client.delete("/users/999")
    assert response.status_code == 404


def test_filter_by_exact(client, sample_users):
    """Test exact match filtering"""
    response = client.get("/users/?name=Alice")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Alice"


def test_filter_icontains(client, sample_users):
    """Test case-insensitive contains filtering"""
    response = client.get("/users/?name__icontains=ali")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Alice"


def test_filter_gte(client, sample_users):
    """Test greater than or equal filtering"""
    response = client.get("/users/?age__gte=30")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # Bob (30) and Charlie (35)


def test_filter_lte(client, sample_users):
    """Test less than or equal filtering"""
    response = client.get("/users/?age__lte=25")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # Alice (25) and Eve (22)


def test_filter_in(client, sample_users):
    """Test IN filtering"""
    response = client.get("/users/?role__in=admin,staff")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # Alice (admin) and Charlie (staff)


def test_ordering_ascending(client, sample_users):
    """Test ascending order"""
    response = client.get("/users/?order_by=age")
    assert response.status_code == 200
    data = response.json()
    ages = [item["age"] for item in data["items"]]
    assert ages == sorted(ages)


def test_ordering_descending(client, sample_users):
    """Test descending order"""
    response = client.get("/users/?order_by=-age")
    assert response.status_code == 200
    data = response.json()
    ages = [item["age"] for item in data["items"]]
    assert ages == sorted(ages, reverse=True)


def test_combined_filters(client, sample_users):
    """Test combining multiple filters"""
    response = client.get("/users/?age__gte=25&role=user&limit=10")
    assert response.status_code == 200
    data = response.json()
    # Should return Bob (30, user) and Diana (28, user)
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["role"] == "user"
        assert item["age"] >= 25