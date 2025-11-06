"""Filtering utilities for CRUD queries"""

from typing import Any, Dict, Type
from sqlalchemy import desc, asc
from sqlalchemy.orm import Query


class FilterOperator:
    """Supported filter operators"""
    EXACT = "exact"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"


class QueryFilter:
    """Build SQLAlchemy filters from query parameters"""
    
    @staticmethod
    def apply_filters(
        query: Query,
        model: Type[Any],
        filters: Dict[str, Any]
    ) -> Query:
        """
        Apply filters to query based on filter dictionary
        
        Format: {field__operator: value}
        Example: {name__icontains: "john", age__gte: 18}
        """
        for filter_key, filter_value in filters.items():
            if filter_value is None:
                continue
                
            # Parse field and operator
            if "__" in filter_key:
                field_name, operator = filter_key.rsplit("__", 1)
            else:
                field_name = filter_key
                operator = FilterOperator.EXACT
            
            # Skip if field doesn't exist on model
            if not hasattr(model, field_name):
                continue
            
            field = getattr(model, field_name)
            
            # Apply operator
            if operator == FilterOperator.EXACT:
                query = query.filter(field == filter_value)
            elif operator == FilterOperator.CONTAINS:
                query = query.filter(field.contains(filter_value))
            elif operator == FilterOperator.ICONTAINS:
                query = query.filter(field.ilike(f"%{filter_value}%"))
            elif operator == FilterOperator.GT:
                query = query.filter(field > filter_value)
            elif operator == FilterOperator.GTE:
                query = query.filter(field >= filter_value)
            elif operator == FilterOperator.LT:
                query = query.filter(field < filter_value)
            elif operator == FilterOperator.LTE:
                query = query.filter(field <= filter_value)
            elif operator == FilterOperator.IN:
                if isinstance(filter_value, str):
                    filter_value = filter_value.split(",")
                query = query.filter(field.in_(filter_value))
            elif operator == FilterOperator.NOT_IN:
                if isinstance(filter_value, str):
                    filter_value = filter_value.split(",")
                query = query.filter(~field.in_(filter_value))
        
        return query
    
    @staticmethod
    def apply_ordering(
        query: Query,
        model: Type[Any],
        order_by: str = None
    ) -> Query:
        """
        Apply ordering to query
        
        Format: field or -field (for descending)
        Example: "created_at" or "-created_at"
        """
        if not order_by:
            return query
        
        # Check for descending order
        if order_by.startswith("-"):
            field_name = order_by[1:]
            order_func = desc
        else:
            field_name = order_by
            order_func = asc
        
        # Apply ordering if field exists
        if hasattr(model, field_name):
            field = getattr(model, field_name)
            query = query.order_by(order_func(field))
        
        return query