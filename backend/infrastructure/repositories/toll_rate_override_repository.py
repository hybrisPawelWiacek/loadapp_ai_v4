"""Repository for toll rate overrides."""
from typing import Optional
from uuid import UUID

from ...domain.entities.transport import TollRateOverride
from ..models.transport_models import TollRateOverrideModel


class TollRateOverrideRepository:
    """Repository for toll rate overrides."""

    def __init__(self, session):
        self._session = session

    def find_by_id(self, id: UUID) -> Optional[TollRateOverride]:
        """Find toll rate override by ID."""
        model = self._session.query(TollRateOverrideModel).filter_by(id=str(id)).first()
        return self._to_entity(model) if model else None

    def find_for_business(
        self,
        business_entity_id: UUID,
        country_code: str,
        vehicle_class: str
    ) -> Optional[TollRateOverride]:
        """Find toll rate override for a business entity, country and vehicle class."""
        model = (
            self._session.query(TollRateOverrideModel)
            .filter_by(
                business_entity_id=str(business_entity_id),
                country_code=country_code,
                vehicle_class=vehicle_class
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def save(self, override: TollRateOverride) -> TollRateOverride:
        """Save a toll rate override."""
        model = TollRateOverrideModel(
            id=str(override.id),
            vehicle_class=override.vehicle_class,
            rate_multiplier=override.rate_multiplier,
            country_code=override.country_code,
            route_type=override.route_type,
            business_entity_id=str(override.business_entity_id)
        )
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: TollRateOverrideModel) -> TollRateOverride:
        """Convert model to domain entity."""
        return TollRateOverride(
            id=UUID(model.id),
            vehicle_class=model.vehicle_class,
            rate_multiplier=model.rate_multiplier,
            country_code=model.country_code,
            route_type=model.route_type,
            business_entity_id=UUID(model.business_entity_id),
            created_at=model.created_at,
            updated_at=model.updated_at
        ) 