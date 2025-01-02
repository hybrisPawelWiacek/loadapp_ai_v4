"""Base repository implementation with common CRUD operations."""
from typing import Generic, Optional, Type, TypeVar, Any, Dict, ContextManager
from uuid import UUID
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, DateTime
from sqlalchemy.exc import SQLAlchemyError

from ..database import Base

ModelType = TypeVar("ModelType", bound=Any)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize repository with model and database session."""
        self._model = model
        self._db = db

    @contextmanager
    def transaction(self) -> ContextManager[Session]:
        """Provide a transactional scope around a series of operations."""
        try:
            # If there's no active transaction, start one
            if not self._db.in_transaction():
                with self._db.begin():
                    yield self._db
            else:
                # If there's already a transaction, just yield the session
                yield self._db
        except Exception:
            # Only rollback if we started the transaction
            if self._db.in_transaction():
                self._db.rollback()
            raise

    def get(self, id: str | UUID) -> Optional[ModelType]:
        """Get entity by ID."""
        try:
            # Convert ID to string, handling both UUID and string IDs
            id_str = str(id)
            
            # Create query
            query = self._db.query(self._model)
            query = query.filter(self._model.id == id_str)
            if hasattr(self._model, 'is_active'):
                query = query.filter(self._model.is_active == True)
            
            # Execute query
            result = query.first()
            if result:
                self._db.refresh(result)
            return result
                
        except (ValueError, AttributeError, TypeError, SQLAlchemyError) as e:
            if self._db.in_transaction():
                self._db.rollback()
            return None

    def find_by_id(self, id: str) -> Optional[ModelType]:
        """Alias for get method to maintain backward compatibility."""
        return self.get(id)

    def list(self, **filters) -> list[ModelType]:
        """List entities with optional filters."""
        # Create query
        query = self._db.query(self._model)
        if hasattr(self._model, 'is_active'):
            query = query.filter(self._model.is_active == True)
        for key, value in filters.items():
            if hasattr(self._model, key):
                query = query.filter(getattr(self._model, key) == value)
        
        # Execute query
        return query.all()

    def find_all_paginated(self, page: int = 1, size: int = 10, **filters) -> Dict[str, Any]:
        """List entities with pagination and optional filters."""
        # Create query
        query = self._db.query(self._model)
        if hasattr(self._model, 'is_active'):
            query = query.filter(self._model.is_active == True)
        for key, value in filters.items():
            if hasattr(self._model, key):
                query = query.filter(getattr(self._model, key) == value)

        # Execute query
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
        self._db.flush()  # Ensure ID is generated
        self._db.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Update existing entity."""
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.utcnow()
        merged = self._db.merge(entity)
        self._db.flush()
        return merged

    def delete(self, id: str) -> bool:
        """Hard delete entity by ID."""
        entity = self.get(id)
        if entity:
            self._db.delete(entity)
            return True
        return False

    def soft_delete(self, id: str) -> bool:
        """Soft delete entity by ID."""
        entity = self.get(id)
        if entity and hasattr(entity, 'is_active'):
            entity.is_active = False
            if hasattr(entity, 'updated_at'):
                entity.updated_at = datetime.utcnow()
            return True
        return False 