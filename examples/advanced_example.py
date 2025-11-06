"""
Advanced example with authentication and role-based permissions

Run with: uvicorn advanced_example:app --reload
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import jwt

from fastapi_autocrud_rishabh import AutoCRUDRouter

# Configuration
SECRET_KEY = "your-secret-key-here"  # Change this!
ALGORITHM = "HS256"

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./advanced_example.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()


# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")  # admin, staff, user
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    role: Optional[str] = "user"


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    username: str
    role: str


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Authentication functions
def create_access_token(username: str, role: str):
    """Create JWT token"""
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow().timestamp() + 3600  # 1 hour
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def add_user_to_request(request: Request, token_data: TokenData = Depends(verify_token)):
    """Middleware to add user data to request state"""
    request.state.user = token_data
    return token_data


def get_user_role(request: Request):
    """Extract user role from request"""
    if hasattr(request.state, "user"):
        return request.state.user.role
    return None


# Create FastAPI app
app = FastAPI(
    title="FastAPI AutoCRUD with Auth",
    description="Advanced example with JWT authentication and role-based permissions",
    version="0.1.0"
)


# Generate CRUD router with permissions
user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    db_session=get_db,
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(add_user_to_request)],  # Require authentication
    roles={
        "delete": ["admin"],  # Only admins can delete
        "update": ["admin", "staff"],  # Admins and staff can update
        "create": ["admin"],  # Only admins can create users
    },
    user_role_getter=get_user_role
)

# Include router
app.include_router(user_router.router)


# Auth endpoints
@app.post("/login")
def login(username: str, role: str = "user"):
    """
    Mock login endpoint - generates JWT token
    In production, verify credentials against database
    """
    token = create_access_token(username=username, role=role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "role": role
    }


@app.get("/")
def root():
    return {
        "message": "FastAPI AutoCRUD with Authentication",
        "docs": "/docs",
        "endpoints": {
            "login": "/login",
            "users": "/users/"
        },
        "instructions": [
            "1. Get token: POST /login with username and role",
            "2. Use token: Add 'Authorization: Bearer <token>' header",
            "3. Try CRUD operations based on your role"
        ]
    }


@app.get("/me")
def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current user info from token"""
    return {
        "username": token_data.username,
        "role": token_data.role
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)