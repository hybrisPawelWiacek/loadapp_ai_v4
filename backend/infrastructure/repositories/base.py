"""Base repository implementation with common CRUD operations."""
from typing import Generic, Optional, Type, TypeVar, Any, Dict, ContextManager
from uuid import UUID
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, DateTime
from sqlalchemy.exc import SQLAlchemyError
import structlog

from ..database import Base

ModelType = TypeVar("ModelType", bound=Any)

# Configure logger
logger = structlog.get_logger()

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
        except SQLAlchemyError as e:
            logger.error("repository.transaction.error", error=str(e))
            # Only rollback if we started the transaction
            if self._db.in_transaction():
                self._db.rollback()
            raise
        except Exception as e:
            logger.error("repository.transaction.unexpected_error", error=str(e))
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
            
            return query.first()
        except SQLAlchemyError as e:
            logger.error("repository.get.error", id=id_str, error=str(e))
            raise
        except Exception as e:
            logger.error("repository.get.unexpected_error", id=id_str, error=str(e))
            raise

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> list[ModelType]:
        """Find all entities matching the filters."""
        try:
            query = self._db.query(self._model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self._model, key):
                        query = query.filter(getattr(self._model, key) == value)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error("repository.find_all.error", filters=filters, error=str(e))
            raise
        except Exception as e:
            logger.error("repository.find_all.unexpected_error", filters=filters, error=str(e))
            raise

    def create(self, entity: ModelType) -> ModelType:
        """Create a new entity."""
        try:
            with self.transaction() as session:
                session.add(entity)
                session.flush()
                return entity
        except SQLAlchemyError as e:
            logger.error("repository.create.error", error=str(e))
            raise
        except Exception as e:
            logger.error("repository.create.unexpected_error", error=str(e))
            raise

    def update(self, entity: ModelType) -> ModelType:
        """Update an existing entity."""
        try:
            with self.transaction() as session:
                session.merge(entity)
                session.flush()
                return entity
        except SQLAlchemyError as e:
            logger.error("repository.update.error", error=str(e))
            raise
        except Exception as e:
            logger.error("repository.update.unexpected_error", error=str(e))
            raise

    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        try:
            with self.transaction() as session:
                entity = self.get(id)
                if entity:
                    session.delete(entity)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error("repository.delete.error", id=id, error=str(e))
            raise
        except Exception as e:
            logger.error("repository.delete.unexpected_error", id=id, error=str(e))
            raise 