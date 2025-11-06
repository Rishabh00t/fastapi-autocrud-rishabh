"""Custom exceptions for AutoCRUD operations"""

from fastapi import HTTPException, status


class CRUDException(HTTPException):
    """Base exception for all CRUD operations"""
    pass


class ItemNotFoundException(CRUDException):
    """Raised when item is not found in database"""
    def __init__(self, detail: str = "Item not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class PermissionDeniedException(CRUDException):
    """Raised when user doesn't have permission"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DatabaseException(CRUDException):
    """Raised when database operation fails"""
    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class UnauthorizedException(CRUDException):
    """Raised when user is not authenticated"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )