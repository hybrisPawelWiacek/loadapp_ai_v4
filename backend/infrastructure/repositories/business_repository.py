"""Repository implementation for business entities."""
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...domain.entities.business import BusinessEntity
from ..models.business_models import BusinessEntityModel
from .base import BaseRepository

# Configure logger
logger = structlog.get_logger()

class SQLBusinessEntityRepository(BaseRepository[BusinessEntityModel]):
    """SQLAlchemy implementation of BusinessEntityRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(BusinessEntityModel, db)
        logger.debug("business_repository.init", session_id=id(db))

    def save(self, entity: BusinessEntity) -> BusinessEntity:
        """Save a business entity."""
        logger.debug("business_repository.save.start", entity_id=str(entity.id))
        try:
            with self.transaction() as session:
                model = BusinessEntityModel(
                    id=str(entity.id),
                    name=entity.name,
                    address=entity.address,
                    contact_info=entity.contact_info,
                    business_type=entity.business_type
                )
                model.set_certifications(entity.certifications)
                model.set_operating_countries(entity.operating_countries)
                model.set_cost_overheads({k: str(v) for k, v in entity.cost_overheads.items()})
                
                result = self.create(model)
                logger.info("business_repository.save.success", entity_id=str(entity.id))
                return self._to_domain(result)
        except SQLAlchemyError as e:
            logger.error("business_repository.save.error", entity_id=str(entity.id), error=str(e))
            raise
        except Exception as e:
            logger.error("business_repository.save.unexpected_error", entity_id=str(entity.id), error=str(e))
            raise

    def find_by_id(self, id: UUID) -> Optional[BusinessEntity]:
        """Find a business entity by ID."""
        logger.debug("business_repository.find_by_id.start", entity_id=str(id))
        try:
            model = self.get(str(id))
            if model:
                logger.info("business_repository.find_by_id.success", entity_id=str(id))
                return self._to_domain(model)
            logger.info("business_repository.find_by_id.not_found", entity_id=str(id))
            return None
        except SQLAlchemyError as e:
            logger.error("business_repository.find_by_id.error", entity_id=str(id), error=str(e))
            raise
        except Exception as e:
            logger.error("business_repository.find_by_id.unexpected_error", entity_id=str(id), error=str(e))
            raise

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[BusinessEntity]:
        """Find all business entities matching the filters."""
        logger.debug("business_repository.find_all.start", filters=filters)
        try:
            models = super().find_all(filters)
            entities = [self._to_domain(model) for model in models]
            logger.info("business_repository.find_all.success", count=len(entities))
            return entities
        except SQLAlchemyError as e:
            logger.error("business_repository.find_all.error", filters=filters, error=str(e))
            raise
        except Exception as e:
            logger.error("business_repository.find_all.unexpected_error", filters=filters, error=str(e))
            raise

    def _to_domain(self, model: BusinessEntityModel) -> BusinessEntity:
        """Convert database model to domain entity."""
        try:
            return BusinessEntity(
                id=UUID(model.id),
                name=model.name,
                address=model.address,
                contact_info=model.get_contact_info(),
                business_type=model.business_type,
                certifications=model.get_certifications(),
                operating_countries=model.get_operating_countries(),
                cost_overheads={k: Decimal(v) for k, v in model.get_cost_overheads().items()},
                default_cost_settings=model.get_default_cost_settings(),
                is_active=model.is_active
            )
        except Exception as e:
            logger.error("business_repository._to_domain.error", model_id=model.id, error=str(e))
            raise


# Alias for backward compatibility
SQLBusinessRepository = SQLBusinessEntityRepository 