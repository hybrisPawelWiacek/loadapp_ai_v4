"""Base repository implementation with common CRUD operations."""
from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from ..database import Base

# Generic type for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize repository with model and database session."""
        self._model = model
        self._db = db

    def get(self, id: str) -> Optional[ModelType]:
        """Get entity by ID."""
        return self._db.query(self._model).filter(self._model.id == id).first()

    def find_by_id(self, id: str) -> Optional[ModelType]:
        """Alias for get method to maintain backward compatibility."""
        return self.get(id)

    def list(self, **filters) -> list[ModelType]:
        """List entities with optional filters."""
        query = self._db.query(self._model)
        for key, value in filters.items():
            if hasattr(self._model, key):
                query = query.filter(getattr(self._model, key) == value)
        return query.all()

    def create(self, entity: ModelType) -> ModelType:
        """Create new entity."""
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Update existing entity."""
        self._db.merge(entity)
        self._db.commit()
        return entity

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        entity = self.get(id)
        if entity:
            self._db.delete(entity)
            self._db.commit()
            return True
        return False 