"""Main AutoCRUDRouter class"""

from typing import Any, Type, Callable, List, Optional, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .generator import CRUDGenerator
from .permissions import PermissionChecker
from .pagination import PaginatedResponse


class AutoCRUDRouter:
    """
    Automatically generate CRUD endpoints for a SQLAlchemy model
    
    Example:
        router = AutoCRUDRouter(
            model=User,
            create_schema=UserCreate,
            read_schema=UserRead,
            db_session=get_db,
            prefix="/users",
            tags=["Users"]
        )
        
        app.include_router(router.router)
    """
    
    def __init__(
        self,
        model: Type[Any],
        create_schema: Type[BaseModel],
        read_schema: Type[BaseModel],
        update_schema: Optional[Type[BaseModel]] = None,
        db_session: Callable = None,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[Depends]] = None,
        roles: Optional[Dict[str, List[str]]] = None,
        user_role_getter: Optional[Callable] = None,
        include_in_schema: bool = True,
    ):
        """
        Initialize AutoCRUDRouter
        
        Args:
            model: SQLAlchemy model class
            create_schema: Pydantic schema for creating items
            read_schema: Pydantic schema for reading items
            update_schema: Pydantic schema for updating (defaults to create_schema)
            db_session: Database session dependency
            prefix: Router prefix (e.g., "/users")
            tags: OpenAPI tags
            dependencies: Global dependencies for all routes
            roles: Dict mapping operations to required roles
                   Example: {"delete": ["admin"], "update": ["admin", "staff"]}
            user_role_getter: Function to extract user role from request
            include_in_schema: Include routes in OpenAPI schema
        """
        self.model = model
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema or create_schema
        self.db_session = db_session
        
        # Create permission checker if roles are provided
        permission_checker = None
        if roles:
            permission_checker = PermissionChecker(
                roles=roles,
                user_role_getter=user_role_getter
            )
        
        # Initialize CRUD generator
        self.generator = CRUDGenerator(
            model=model,
            create_schema=create_schema,
            read_schema=read_schema,
            update_schema=self.update_schema,
            db_session=db_session,
            permission_checker=permission_checker,
        )
        
        # Create FastAPI router
        self.router = APIRouter(
            prefix=prefix,
            tags=tags or [model.__name__],
            dependencies=dependencies,
            include_in_schema=include_in_schema,
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all CRUD routes"""
        model_name = self.model.__name__
        
        # CREATE
        self.router.add_api_route(
            "/",
            self.generator.create_item(),
            methods=["POST"],
            response_model=self.read_schema,
            status_code=201,
            summary=f"Create {model_name}",
            description=f"Create a new {model_name} item",
        )
        
        # LIST
        self.router.add_api_route(
            "/",
            self.generator.list_items(),
            methods=["GET"],
            response_model=PaginatedResponse[self.read_schema],
            summary=f"List {model_name}s",
            description=f"List all {model_name} items with pagination and filtering",
        )
        
        # GET by ID
        self.router.add_api_route(
            "/{item_id}",
            self.generator.get_item(),
            methods=["GET"],
            response_model=self.read_schema,
            summary=f"Get {model_name}",
            description=f"Get a {model_name} by ID",
        )
        
        # UPDATE
        self.router.add_api_route(
            "/{item_id}",
            self.generator.update_item(),
            methods=["PUT"],
            response_model=self.read_schema,
            summary=f"Update {model_name}",
            description=f"Update a {model_name} by ID",
        )
        
        # DELETE
        self.router.add_api_route(
            "/{item_id}",
            self.generator.delete_item(),
            methods=["DELETE"],
            response_model=dict,
            summary=f"Delete {model_name}",
            description=f"Delete a {model_name} by ID",
        )