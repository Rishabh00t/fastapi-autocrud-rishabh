"""Test role-based permissions"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from .conftest import User, UserCreate, UserRead, UserUpdate


class MockUser:
    """Mock user for testing"""
    def __init__(self, role: str):
        self.role = role


@pytest.fixture
def app_with_permissions(get_db):
    """Create FastAPI app with role-based permissions"""
    from fastapi_autocrud_rishabh import AutoCRUDRouter
    
    app = FastAPI()
    
    def get_user_role(request: Request):
        """Extract role from request state"""
        if hasattr(request.state, "user"):
            return request.state.user.role
        return None
    
    user_router = AutoCRUDRouter(
        model=User,
        create_schema=UserCreate,
        read_schema=UserRead,
        update_schema=UserUpdate,
        db_session=get_db,
        prefix="/users",
        roles={
            "delete": ["admin"],
            "update": ["admin", "staff"],
            "create": ["admin", "staff", "user"],
        },
        user_role_getter=get_user_role
    )
    
    app.include_router(user_router.router)
    return app


def test_admin_can_delete(app_with_permissions, sample_users):
    """Test admin can delete users"""
    client = TestClient(app_with_permissions)
    
    # Mock admin user
    def mock_request(request: Request):
        request.state.user = MockUser(role="admin")
    
    # Apply middleware to add user to request
    @app_with_permissions.middleware("http")
    async def add_user(request: Request, call_next):
        request.state.user = MockUser(role="admin")
        response = await call_next(request)
        return response
    
    user_id = sample_users[0].id
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200


def test_user_cannot_delete(app_with_permissions, sample_users):
    """Test regular user cannot delete"""
    client = TestClient(app_with_permissions)
    
    @app_with_permissions.middleware("http")
    async def add_user(request: Request, call_next):
        request.state.user = MockUser(role="user")
        response = await call_next(request)
        return response
    
    user_id = sample_users[0].id
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]


def test_staff_can_update(app_with_permissions, sample_users):
    """Test staff can update users"""
    client = TestClient(app_with_permissions)
    
    @app_with_permissions.middleware("http")
    async def add_user(request: Request, call_next):
        request.state.user = MockUser(role="staff")
        response = await call_next(request)
        return response
    
    user_id = sample_users[0].id
    response = client.put(
        f"/users/{user_id}",
        json={"name": "Updated"}
    )
    assert response.status_code == 200


def test_user_cannot_update(app_with_permissions, sample_users):
    """Test regular user cannot update"""
    client = TestClient(app_with_permissions)
    
    @app_with_permissions.middleware("http")
    async def add_user(request: Request, call_next):
        request.state.user = MockUser(role="user")
        response = await call_next(request)
        return response
    
    user_id = sample_users[0].id
    response = client.put(
        f"/users/{user_id}",
        json={"name": "Updated"}
    )
    assert response.status_code == 403


def test_all_roles_can_read(sample_users, get_db):
    """Test all roles can read (no permission restriction)"""
    from fastapi_autocrud_rishabh import AutoCRUDRouter
    
    # Test each role in separate app instances
    for role in ["admin", "staff", "user"]:
        app = FastAPI()
        
        def get_user_role(request: Request):
            if hasattr(request.state, "user"):
                return request.state.user.role
            return None
        
        user_router = AutoCRUDRouter(
            model=User,
            create_schema=UserCreate,
            read_schema=UserRead,
            update_schema=UserUpdate,
            db_session=get_db,
            prefix="/users",
            roles={
                "delete": ["admin"],
                "update": ["admin", "staff"],
                "create": ["admin", "staff", "user"],
            },
            user_role_getter=get_user_role
        )
        
        app.include_router(user_router.router)
        
        # Add middleware before creating client
        @app.middleware("http")
        async def add_user(request: Request, call_next):
            request.state.user = MockUser(role=role)
            response = await call_next(request)
            return response
        
        client = TestClient(app)
        response = client.get("/users/")
        assert response.status_code == 200