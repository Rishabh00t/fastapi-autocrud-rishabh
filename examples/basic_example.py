"""
Basic example of using fastapi_autocrud_rishabh

Run with: uvicorn basic_example:app --reload
Then visit: http://localhost:8000/docs
"""

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from fastapi_autocrud_rishabh import AutoCRUDRouter

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    author = Column(String)
    published = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# Pydantic Schemas
class UserCreate(BaseModel):
    name: str
    email: str
    age: int
    role: Optional[str] = "user"


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    age: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    title: str
    content: str
    author: str
    published: Optional[int] = 0


class PostRead(BaseModel):
    id: int
    title: str
    content: str
    author: str
    published: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create FastAPI app
app = FastAPI(
    title="FastAPI AutoCRUD Example",
    description="Example using fastapi-autocrud-rishabh package",
    version="0.1.0"
)


# Generate CRUD routers
user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    db_session=get_db,
    prefix="/users",
    tags=["Users"]
)

post_router = AutoCRUDRouter(
    model=Post,
    create_schema=PostCreate,
    read_schema=PostRead,
    db_session=get_db,
    prefix="/posts",
    tags=["Posts"]
)

# Include routers
app.include_router(user_router.router)
app.include_router(post_router.router)


@app.get("/")
def root():
    return {
        "message": "FastAPI AutoCRUD Example",
        "docs": "/docs",
        "endpoints": {
            "users": "/users/",
            "posts": "/posts/"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)