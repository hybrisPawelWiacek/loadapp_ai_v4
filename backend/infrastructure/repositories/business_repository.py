"""Repository implementation for business entities."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ...domain.entities.business import BusinessEntity
from ..models.business_models import BusinessEntityModel
from .base import BaseRepository


class SQLBusinessEntityRepository(BaseRepository[BusinessEntityModel]):
    """SQLAlchemy implementation of BusinessEntityRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(BusinessEntityModel, db)

    def save(self, entity: BusinessEntity) -> BusinessEntity:
        """Save a business entity."""
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
        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[BusinessEntity]:
        """Find a business entity by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: BusinessEntityModel) -> BusinessEntity:
        """Convert model to domain entity."""
        return BusinessEntity(
            id=UUID(model.id),
            name=model.name,
            address=model.address,
            contact_info=model.get_contact_info(),
            business_type=model.business_type,
            certifications=model.get_certifications(),
            operating_countries=model.get_operating_countries(),
            cost_overheads={k: Decimal(v) for k, v in model.get_cost_overheads().items()}
        )


# Alias for backward compatibility
SQLBusinessRepository = SQLBusinessEntityRepository 