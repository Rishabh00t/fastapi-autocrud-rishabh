"""Pagination utilities for CRUD operations"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    limit: int
    offset: int
    
    class Config:
        arbitrary_types_allowed = True


class PaginationParams:
    """Pagination parameters for queries"""
    def __init__(
        self,
        limit: int = 100,
        offset: int = 0,
        max_limit: int = 1000
    ):
        self.limit = min(limit, max_limit) if limit > 0 else max_limit
        self.offset = max(offset, 0)
    
    def apply(self, query):
        """Apply pagination to SQLAlchemy query"""
        return query.limit(self.limit).offset(self.offset)