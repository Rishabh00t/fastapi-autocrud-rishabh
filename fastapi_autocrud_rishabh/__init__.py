"""
fastapi_autocrud_rishabh - Auto-generate CRUD APIs for FastAPI with SQLAlchemy
"""

__version__ = "0.1.0"
__author__ = "Rishabh"

from .router import AutoCRUDRouter
from .exceptions import (
    CRUDException,
    ItemNotFoundException,
    PermissionDeniedException,
    DatabaseException,
)

__all__ = [
    "AutoCRUDRouter",
    "CRUDException",
    "ItemNotFoundException",
    "PermissionDeniedException",
    "DatabaseException",
]