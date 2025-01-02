"""Base repository implementation with common CRUD operations."""
from typing import Generic, Optional, Type, TypeVar, Any, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, DateTime

from ..database import Base

ModelType = TypeVar("ModelType", bound=Any)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize repository with model and database session."""
        self._model = model
        self._db = db

    def get(self, id: str) -> Optional[ModelType]:
        """Get entity by ID."""
        query = self._db.query(self._model)
        if isinstance(id, UUID):
            query = query.filter(self._model.id == str(id))
        else:
            query = query.filter(self._model.id == id)
        if hasattr(self._model, 'is_active'):
            query = query.filter(self._model.is_active == True)
        return query.first()

    def find_by_id(self, id: str) -> Optional[ModelType]:
        """Alias for get method to maintain backward compatibility."""
        return self.get(id)

    def list(self, **filters) -> list[ModelType]:
        """List entities with optional filters."""
        query = self._db.query(self._model)
        if hasattr(self._model, 'is_active'):
            query = query.filter(self._model.is_active == True)
        for key, value in filters.items():
            if hasattr(self._model, key):
                query = query.filter(getattr(self._model, key) == value)
        return query.all()

    def find_all_paginated(self, page: int = 1, size: int = 10, **filters) -> Dict[str, Any]:
        """List entities with pagination and optional filters."""
        query = self._db.query(self._model)
        if hasattr(self._model, 'is_active'):
            query = query.filter(self._model.is_active == True)
        for key, value in filters.items():
            if hasattr(self._model, key):
                query = query.filter(getattr(self._model, key) == value)

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }

    def create(self, entity: ModelType) -> ModelType:
        """Create new entity."""
        if hasattr(entity, 'is_active'):
            entity.is_active = True
        if hasattr(entity, 'created_at') and entity.created_at is None:
            entity.created_at = datetime.utcnow()
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Update existing entity."""
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.utcnow()
        self._db.merge(entity)
        self._db.commit()
        return entity

    def delete(self, id: str) -> bool:
        """Hard delete entity by ID."""
        entity = self.get(id)
        if entity:
            self._db.delete(entity)
            self._db.commit()
            return True
        return False

    def soft_delete(self, id: str) -> bool:
        """Soft delete entity by ID."""
        entity = self.get(id)
        if entity and hasattr(entity, 'is_active'):
            entity.is_active = False
            if hasattr(entity, 'updated_at'):
                entity.updated_at = datetime.utcnow()
            self._db.commit()
            return True
        return False 