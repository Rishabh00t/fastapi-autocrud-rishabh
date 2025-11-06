"""Utility functions for AutoCRUD"""

from typing import Any, Type
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect


def get_primary_key_name(model: Type[Any]) -> str:
    """Get the primary key column name of a SQLAlchemy model"""
    mapper = inspect(model)
    primary_keys = [key.name for key in mapper.primary_key]
    if not primary_keys:
        raise ValueError(f"Model {model.__name__} has no primary key")
    return primary_keys[0]  # Return first primary key


def get_model_fields(model: Type[Any]) -> list:
    """Get all column names from SQLAlchemy model"""
    mapper = inspect(model)
    return [column.key for column in mapper.columns]


def model_to_dict(obj: Any) -> dict:
    """Convert SQLAlchemy model instance to dictionary"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}