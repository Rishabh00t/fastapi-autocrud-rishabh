import pytest
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Test Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


# Test Schemas
class UserCreate(BaseModel):
    name: str
    email: str
    age: int
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    age: int
    role: str
    
    class Config:
        from_attributes = True
        # Pydantic v2 compatibility
        orm_mode = True


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def get_db(db_session):
    """Database dependency override"""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db


@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing"""
    users = [
        User(name="Alice", email="alice@example.com", age=25, role="admin"),
        User(name="Bob", email="bob@example.com", age=30, role="user"),
        User(name="Charlie", email="charlie@example.com", age=35, role="staff"),
        User(name="Diana", email="diana@example.com", age=28, role="user"),
        User(name="Eve", email="eve@example.com", age=22, role="user"),
    ]
    for user in users:
        db_session.add(user)
    db_session.commit()
    
    for user in users:
        db_session.refresh(user)
    
    return users