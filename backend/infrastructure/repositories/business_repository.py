"""Repository implementation for business entities."""
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import json

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

    def save(self, business_entity: BusinessEntity) -> BusinessEntity:
        """Save a business entity to the database."""
        logger.debug("business_repository.save.start", entity_id=str(business_entity.id))
        try:
            with self.transaction() as session:
                # Check if entity already exists
                existing = session.query(BusinessEntityModel).filter_by(id=str(business_entity.id)).first()
                
                if existing:
                    # Update existing entity
                    logger.debug("business_repository.save.updating", entity_id=str(business_entity.id))
                    existing.name = business_entity.name
                    existing.address = business_entity.address
                    existing.set_contact_info(business_entity.contact_info)
                    existing.business_type = business_entity.business_type
                    existing.set_certifications(business_entity.certifications)
                    existing.set_operating_countries(business_entity.operating_countries)
                    # Convert Decimal values to strings before setting
                    cost_overheads_str = {k: str(v) for k, v in business_entity.cost_overheads.items()}
                    existing.set_cost_overheads(cost_overheads_str)
                    # Only set default_cost_settings if it exists in the model
                    if hasattr(business_entity, 'default_cost_settings') and business_entity.default_cost_settings:
                        # Convert any Decimal values in default_cost_settings
                        default_settings_str = self._convert_decimals_to_str(business_entity.default_cost_settings)
                        existing.set_default_cost_settings(default_settings_str)
                    existing.is_active = business_entity.is_active
                    model = existing
                else:
                    # Create new entity
                    logger.debug("business_repository.save.creating", entity_id=str(business_entity.id))
                    # Convert Decimal values to strings
                    cost_overheads_str = {k: str(v) for k, v in business_entity.cost_overheads.items()}
                    model_data = {
                        'id': str(business_entity.id),  # Convert UUID to string
                        'name': business_entity.name,
                        'address': business_entity.address,
                        'contact_info': business_entity.contact_info,
                        'business_type': business_entity.business_type,
                        'certifications': business_entity.certifications,
                        'operating_countries': business_entity.operating_countries,
                        'cost_overheads': cost_overheads_str,
                        'is_active': business_entity.is_active
                    }
                    # Only add default_cost_settings if it exists and has value
                    if hasattr(business_entity, 'default_cost_settings') and business_entity.default_cost_settings:
                        # Convert any Decimal values in default_cost_settings
                        default_settings_str = self._convert_decimals_to_str(business_entity.default_cost_settings)
                        model_data['default_cost_settings'] = default_settings_str
                    
                    model = BusinessEntityModel(**model_data)
                    session.add(model)

                session.commit()
                logger.info("business_repository.save.success", entity_id=str(business_entity.id))
                return self._to_domain(model)

        except SQLAlchemyError as e:
            logger.error("business_repository.save.error", entity_id=str(business_entity.id), error=str(e))
            raise
        except Exception as e:
            logger.error("business_repository.save.unexpected_error", entity_id=str(business_entity.id), error=str(e))
            raise

    def _convert_decimals_to_str(self, data: Dict) -> Dict:
        """Convert all Decimal values in a dictionary to strings recursively."""
        result = {}
        for k, v in data.items():
            if isinstance(v, Decimal):
                result[k] = str(v)
            elif isinstance(v, dict):
                result[k] = self._convert_decimals_to_str(v)
            elif isinstance(v, list):
                result[k] = [str(x) if isinstance(x, Decimal) else x for x in v]
            else:
                result[k] = v
        return result

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
            logger.error("business_repository._to_domain.error", error=str(e))
            raise RepositoryError(f"Error converting model to domain entity: {str(e)}") from e

# Alias for backward compatibility
SQLBusinessRepository = SQLBusinessEntityRepository 