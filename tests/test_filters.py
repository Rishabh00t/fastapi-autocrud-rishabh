"""Test filtering and ordering functionality"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from .conftest import User, UserCreate, UserRead


@pytest.fixture
def app(get_db):
    """Create FastAPI app with AutoCRUD router"""
    from fastapi_autocrud_rishabh import AutoCRUDRouter
    
    app = FastAPI()
    
    user_router = AutoCRUDRouter(
        model=User,
        create_schema=UserCreate,
        read_schema=UserRead,
        db_session=get_db,
        prefix="/users",
    )
    
    app.include_router(user_router.router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestFiltering:
    """Test query filtering"""
    
    def test_exact_match(self, client, sample_users):
        """Test exact match filtering"""
        response = client.get("/users/?email=alice@example.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["email"] == "alice@example.com"
    
    def test_contains_case_sensitive(self, client, sample_users):
        """Test case-sensitive contains"""
        response = client.get("/users/?name__contains=li")
        assert response.status_code == 200
        data = response.json()
        # Should match Alice and Charlie
        assert len(data["items"]) >= 1
    
    def test_icontains_case_insensitive(self, client, sample_users):
        """Test case-insensitive contains"""
        response = client.get("/users/?name__icontains=ALICE")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Alice"
    
    def test_greater_than(self, client, sample_users):
        """Test greater than filter"""
        response = client.get("/users/?age__gt=28")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["age"] > 28
    
    def test_greater_than_equal(self, client, sample_users):
        """Test greater than or equal filter"""
        response = client.get("/users/?age__gte=28")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["age"] >= 28
    
    def test_less_than(self, client, sample_users):
        """Test less than filter"""
        response = client.get("/users/?age__lt=30")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["age"] < 30
    
    def test_less_than_equal(self, client, sample_users):
        """Test less than or equal filter"""
        response = client.get("/users/?age__lte=25")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["age"] <= 25
    
    def test_in_filter(self, client, sample_users):
        """Test IN filter with multiple values"""
        response = client.get("/users/?role__in=admin,staff")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["role"] in ["admin", "staff"]
    
    def test_not_in_filter(self, client, sample_users):
        """Test NOT IN filter"""
        response = client.get("/users/?role__not_in=admin,staff")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["role"] not in ["admin", "staff"]
    
    def test_multiple_filters(self, client, sample_users):
        """Test combining multiple filters"""
        response = client.get("/users/?age__gte=25&age__lte=30&role=user")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert 25 <= item["age"] <= 30
            assert item["role"] == "user"
    
    def test_filter_nonexistent_field(self, client, sample_users):
        """Test filtering by non-existent field (should be ignored)"""
        response = client.get("/users/?nonexistent__exact=value")
        assert response.status_code == 200
        data = response.json()
        # Should return all users since filter is ignored
        assert len(data["items"]) == 5


class TestOrdering:
    """Test query ordering"""
    
    def test_order_ascending(self, client, sample_users):
        """Test ascending order"""
        response = client.get("/users/?order_by=age")
        assert response.status_code == 200
        data = response.json()
        ages = [item["age"] for item in data["items"]]
        assert ages == sorted(ages)
    
    def test_order_descending(self, client, sample_users):
        """Test descending order"""
        response = client.get("/users/?order_by=-age")
        assert response.status_code == 200
        data = response.json()
        ages = [item["age"] for item in data["items"]]
        assert ages == sorted(ages, reverse=True)
    
    def test_order_by_string_field(self, client, sample_users):
        """Test ordering by string field"""
        response = client.get("/users/?order_by=name")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == sorted(names)
    
    def test_order_by_nonexistent_field(self, client, sample_users):
        """Test ordering by non-existent field (should be ignored)"""
        response = client.get("/users/?order_by=nonexistent")
        assert response.status_code == 200
        # Should succeed without ordering


class TestPaginationWithFilters:
    """Test pagination combined with filters"""
    
    def test_pagination_with_filter(self, client, sample_users):
        """Test pagination on filtered results"""
        # Filter for users with role='user' (3 users)
        response = client.get("/users/?role=user&limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3  # Total matching filter
        
        # Get next page
        response = client.get("/users/?role=user&limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 3
    
    def test_ordering_with_pagination(self, client, sample_users):
        """Test ordering combined with pagination"""
        response = client.get("/users/?order_by=-age&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        # Should get two oldest users
        ages = [item["age"] for item in data["items"]]
        assert ages[0] >= ages[1]
    
    def test_complex_query(self, client, sample_users):
        """Test complex query with filter, order, and pagination"""
        response = client.get(
            "/users/?age__gte=25&order_by=-age&limit=2&offset=0"
        )
        assert response.status_code == 200
        data = response.json()
        
        # All should be age >= 25
        for item in data["items"]:
            assert item["age"] >= 25
        
        # Should be ordered descending
        if len(data["items"]) >= 2:
            assert data["items"][0]["age"] >= data["items"][1]["age"]