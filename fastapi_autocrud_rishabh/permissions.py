"""Permission handling for CRUD operations"""

from typing import Dict, List, Optional, Callable
from fastapi import Request
from .exceptions import PermissionDeniedException


class PermissionChecker:
    """Check permissions for CRUD operations"""
    
    def __init__(
        self,
        roles: Optional[Dict[str, List[str]]] = None,
        user_role_getter: Optional[Callable] = None
    ):
        """
        Initialize permission checker
        
        Args:
            roles: Dict mapping operation to required roles
                   Example: {"delete": ["admin"], "update": ["admin", "staff"]}
            user_role_getter: Function to extract user role from request
                             Example: lambda request: request.state.user.role
        """
        self.roles = roles or {}
        self.user_role_getter = user_role_getter or self._default_role_getter
    
    def _default_role_getter(self, request: Request) -> Optional[str]:
        """Default implementation to get user role from request"""
        # Try common patterns
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "role"):
                return user.role
            if isinstance(user, dict) and "role" in user:
                return user["role"]
        return None
    
    def check_permission(self, request: Request, operation: str) -> bool:
        """
        Check if user has permission for operation
        
        Args:
            request: FastAPI request object
            operation: Operation name (create, read, update, delete, list)
        
        Returns:
            True if permitted
            
        Raises:
            PermissionDeniedException if not permitted
        """
        # If no roles defined for this operation, allow access
        if operation not in self.roles:
            return True
        
        required_roles = self.roles[operation]
        user_role = self.user_role_getter(request)
        
        # If user has no role or doesn't match required roles
        if not user_role or user_role not in required_roles:
            raise PermissionDeniedException(
                detail=f"Permission denied. Required roles: {', '.join(required_roles)}"
            )
        
        return True
    
    def create_dependency(self, operation: str):
        """Create FastAPI dependency for permission checking"""
        async def permission_dependency(request: Request):
            self.check_permission(request, operation)
        return permission_dependency