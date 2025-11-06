"""CRUD endpoint generator"""

from typing import Any, Type, Callable, List, Optional, Dict
from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .exceptions import ItemNotFoundException, DatabaseException
from .pagination import PaginationParams, PaginatedResponse
from .filters import QueryFilter
from .permissions import PermissionChecker
from .utils import get_primary_key_name


class CRUDGenerator:
    """Generate CRUD operations for a model"""
    
    def __init__(
        self,
        model: Type[Any],
        create_schema: Type[BaseModel],
        read_schema: Type[BaseModel],
        update_schema: Optional[Type[BaseModel]] = None,
        db_session: Callable = None,
        permission_checker: Optional[PermissionChecker] = None,
    ):
        self.model = model
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema or create_schema
        self.db_session = db_session
        self.permission_checker = permission_checker
        self.pk_name = get_primary_key_name(model)
    
    def create_item(self):
        """Generate CREATE endpoint"""
        async def endpoint(
            item: self.create_schema,
            request: Request,
            db: Session = Depends(self.db_session)
        ):
            # Check permissions
            if self.permission_checker:
                self.permission_checker.check_permission(request, "create")
            
            try:
                # Create model instance from schema
                db_item = self.model(**item.dict())
                db.add(db_item)
                db.commit()
                db.refresh(db_item)
                
                # Return as read schema
                return self.read_schema.from_orm(db_item)
            except Exception as e:
                db.rollback()
                raise DatabaseException(detail=f"Failed to create item: {str(e)}")
        
        return endpoint
    
    def list_items(self):
        """Generate LIST endpoint with pagination and filtering"""
        async def endpoint(
            request: Request,
            db: Session = Depends(self.db_session),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            order_by: Optional[str] = Query(None),
        ):
            # Check permissions
            if self.permission_checker:
                self.permission_checker.check_permission(request, "list")
            
            try:
                # Build base query
                query = db.query(self.model)
                
                # Apply filters from query parameters
                filters = {}
                for key, value in request.query_params.items():
                    if key not in ["limit", "offset", "order_by"]:
                        filters[key] = value
                
                query = QueryFilter.apply_filters(query, self.model, filters)
                
                # Apply ordering
                query = QueryFilter.apply_ordering(query, self.model, order_by)
                
                # Get total count before pagination
                total = query.count()
                
                # Apply pagination
                pagination = PaginationParams(limit=limit, offset=offset)
                query = pagination.apply(query)
                
                # Execute query
                items = query.all()
                
                # Convert to read schema
                items_data = [self.read_schema.from_orm(item) for item in items]
                
                return PaginatedResponse(
                    items=items_data,
                    total=total,
                    limit=limit,
                    offset=offset
                )
            except Exception as e:
                raise DatabaseException(detail=f"Failed to list items: {str(e)}")
        
        return endpoint
    
    def get_item(self):
        """Generate GET by ID endpoint"""
        async def endpoint(
            item_id: int,
            request: Request,
            db: Session = Depends(self.db_session)
        ):
            # Check permissions
            if self.permission_checker:
                self.permission_checker.check_permission(request, "read")
            
            try:
                item = db.query(self.model).filter(
                    getattr(self.model, self.pk_name) == item_id
                ).first()
                
                if not item:
                    raise ItemNotFoundException(
                        detail=f"{self.model.__name__} with id {item_id} not found"
                    )
                
                return self.read_schema.from_orm(item)
            except ItemNotFoundException:
                raise
            except Exception as e:
                raise DatabaseException(detail=f"Failed to retrieve item: {str(e)}")
        
        return endpoint
    
    def update_item(self):
        """Generate UPDATE endpoint"""
        async def endpoint(
            item_id: int,
            item: self.update_schema,
            request: Request,
            db: Session = Depends(self.db_session)
        ):
            # Check permissions
            if self.permission_checker:
                self.permission_checker.check_permission(request, "update")
            
            try:
                db_item = db.query(self.model).filter(
                    getattr(self.model, self.pk_name) == item_id
                ).first()
                
                if not db_item:
                    raise ItemNotFoundException(
                        detail=f"{self.model.__name__} with id {item_id} not found"
                    )
                
                # Update fields
                update_data = item.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(db_item, field, value)
                
                db.commit()
                db.refresh(db_item)
                
                return self.read_schema.from_orm(db_item)
            except ItemNotFoundException:
                raise
            except Exception as e:
                db.rollback()
                raise DatabaseException(detail=f"Failed to update item: {str(e)}")
        
        return endpoint
    
    def delete_item(self):
        """Generate DELETE endpoint"""
        async def endpoint(
            item_id: int,
            request: Request,
            db: Session = Depends(self.db_session)
        ):
            # Check permissions
            if self.permission_checker:
                self.permission_checker.check_permission(request, "delete")
            
            try:
                db_item = db.query(self.model).filter(
                    getattr(self.model, self.pk_name) == item_id
                ).first()
                
                if not db_item:
                    raise ItemNotFoundException(
                        detail=f"{self.model.__name__} with id {item_id} not found"
                    )
                
                db.delete(db_item)
                db.commit()
                
                return {"detail": "Item deleted successfully", "id": item_id}
            except ItemNotFoundException:
                raise
            except Exception as e:
                db.rollback()
                raise DatabaseException(detail=f"Failed to delete item: {str(e)}")
        
        return endpoint