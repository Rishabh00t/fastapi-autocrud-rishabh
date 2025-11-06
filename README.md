# fastapi-autocrud-rishabh

🚀 Automatically generate fully functional CRUD APIs for FastAPI applications using SQLAlchemy models and Pydantic schemas — without writing repetitive endpoint code.

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

✨ **Auto-generate CRUD endpoints** - Create, Read, Update, Delete with one line  
📄 **Built-in Pagination** - Limit/offset pagination out of the box  
🔍 **Advanced Filtering** - Support for multiple filter operators (`icontains`, `gte`, `in`, etc.)  
📊 **Ordering** - Sort by any field ascending or descending  
🔐 **Role-Based Access Control** - Optional permission system  
📚 **Auto OpenAPI Docs** - Swagger UI documentation generated automatically  
⚡ **Zero Dependencies** - Only requires FastAPI and SQLAlchemy  

## Installation

```bash
pip install fastapi-autocrud-rishabh
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from fastapi_autocrud_rishabh import AutoCRUDRouter

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    age: int
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI App
app = FastAPI()

# Generate CRUD Router (1 line!)
user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    db_session=get_db,
    prefix="/users",
    tags=["Users"]
)

# Include router
app.include_router(user_router.router)
```

That's it! You now have 5 endpoints:

- `POST /users/` - Create user
- `GET /users/` - List users (with pagination & filters)
- `GET /users/{id}` - Get user by ID
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

## Advanced Usage

### Filtering & Pagination

```bash
# Pagination
GET /users/?limit=25&offset=0

# Filtering
GET /users/?name__icontains=john&age__gte=18

# Ordering
GET /users/?order_by=-created_at

# Combine all
GET /users/?limit=10&age__gte=21&name__icontains=alice&order_by=-id
```

### Supported Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `exact` | Exact match (default) | `name=John` |
| `contains` | Case-sensitive contains | `name__contains=oh` |
| `icontains` | Case-insensitive contains | `name__icontains=JOHN` |
| `gt` | Greater than | `age__gt=18` |
| `gte` | Greater than or equal | `age__gte=18` |
| `lt` | Less than | `age__lt=65` |
| `lte` | Less than or equal | `age__lte=65` |
| `in` | In list | `id__in=1,2,3` |
| `not_in` | Not in list | `status__not_in=banned,deleted` |

### Role-Based Access Control

```python
from fastapi import Request

# Define role getter
def get_user_role(request: Request):
    return request.state.user.role  # Adjust based on your auth system

# Create router with role restrictions
user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    db_session=get_db,
    prefix="/users",
    roles={
        "delete": ["admin"],
        "update": ["admin", "staff"],
        "create": ["admin", "staff", "user"]
    },
    user_role_getter=get_user_role
)
```

### Global Dependencies (JWT Auth)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Your token verification logic
    if not valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Add to all endpoints
user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    db_session=get_db,
    prefix="/users",
    dependencies=[Depends(verify_token)]
)
```

### Custom Update Schema

```python
class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None

user_router = AutoCRUDRouter(
    model=User,
    create_schema=UserCreate,
    read_schema=UserRead,
    update_schema=UserUpdate,  # Separate update schema
    db_session=get_db,
    prefix="/users"
)
```

## Response Format

### List Endpoint Response
```json
{
  "items": [
    {"id": 1, "name": "John", "email": "john@example.com", "age": 25},
    {"id": 2, "name": "Jane", "email": "jane@example.com", "age": 30}
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

### Error Responses
```json
{
  "detail": "Item not found"
}
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/fastapi-autocrud-rishabh.git
cd fastapi-autocrud-rishabh

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=fastapi_autocrud_rishabh --cov-report=html

# Format code
black .
isort .

# Lint
flake8 fastapi_autocrud_rishabh
```

## Publishing to PyPI

```bash
# Build package
python -m pip install build twine
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Roadmap

- ✅ v0.1.0 - Initial release with sync SQLAlchemy support
- ⏳ v0.2.0 - Async SQLAlchemy support
- ⏳ v0.3.0 - Relationship support (1-to-many, many-to-many)
- ⏳ v0.4.0 - Pydantic v2 support
- ⏳ v1.0.0 - Production ready with full test coverage

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Rishabh**

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/fastapi-autocrud-rishabh/issues) on GitHub.