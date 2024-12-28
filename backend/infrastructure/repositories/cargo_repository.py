"""Repository implementations for cargo and cost-related entities."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ...domain.entities.cargo import (
    Cargo, CostSettings, CostBreakdown, Offer
)
from ..models.cargo_models import (
    CargoModel, CostSettingsModel,
    CostBreakdownModel, OfferModel
)
from .base import BaseRepository


class SQLCargoRepository(BaseRepository[CargoModel]):
    """SQLAlchemy implementation of CargoRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(CargoModel, db)

    def save(self, cargo: Cargo) -> Cargo:
        """Save a cargo instance."""
        model = CargoModel(
            id=str(cargo.id),
            weight=cargo.weight,
            value=str(cargo.value),
            special_requirements=cargo.special_requirements
        )
        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Cargo]:
        """Find a cargo by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: CargoModel) -> Cargo:
        """Convert model to domain entity."""
        return Cargo(
            id=UUID(model.id),
            weight=model.weight,
            value=Decimal(model.value),
            special_requirements=model.get_special_requirements()
        )


class SQLCostSettingsRepository(BaseRepository[CostSettingsModel]):
    """SQLAlchemy implementation of CostSettingsRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(CostSettingsModel, db)

    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings."""
        model = CostSettingsModel(
            id=str(settings.id),
            route_id=str(settings.route_id),
            business_entity_id=str(settings.business_entity_id),
            enabled_components=settings.enabled_components,
            rates={k: str(v) for k, v in settings.rates.items()}
        )
        return self._to_domain(self.create(model))

    def find_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Find cost settings by route ID."""
        model = self.list(route_id=str(route_id))[0] if self.list(route_id=str(route_id)) else None
        return self._to_domain(model) if model else None

    def _to_domain(self, model: CostSettingsModel) -> CostSettings:
        """Convert model to domain entity."""
        return CostSettings(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            business_entity_id=UUID(model.business_entity_id),
            enabled_components=model.get_enabled_components(),
            rates={k: Decimal(v) for k, v in model.get_rates().items()}
        )


class SQLCostBreakdownRepository(BaseRepository[CostBreakdownModel]):
    """SQLAlchemy implementation of CostBreakdownRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(CostBreakdownModel, db)

    def save(self, breakdown: CostBreakdown) -> CostBreakdown:
        """Save cost breakdown."""
        model = CostBreakdownModel(
            id=str(UUID()),
            route_id=str(breakdown.route_id),
            fuel_costs={k: str(v) for k, v in breakdown.fuel_costs.items()},
            toll_costs={k: str(v) for k, v in breakdown.toll_costs.items()},
            driver_costs=str(breakdown.driver_costs),
            overhead_costs=str(breakdown.overhead_costs),
            timeline_event_costs={k: str(v) for k, v in breakdown.timeline_event_costs.items()},
            total_cost=str(breakdown.total_cost)
        )
        return self._to_domain(self.create(model))

    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find cost breakdown by route ID."""
        model = self.list(route_id=str(route_id))[0] if self.list(route_id=str(route_id)) else None
        return self._to_domain(model) if model else None

    def _to_domain(self, model: CostBreakdownModel) -> CostBreakdown:
        """Convert model to domain entity."""
        return CostBreakdown(
            route_id=UUID(model.route_id),
            fuel_costs={k: Decimal(v) for k, v in model.get_fuel_costs().items()},
            toll_costs={k: Decimal(v) for k, v in model.get_toll_costs().items()},
            driver_costs=Decimal(model.driver_costs),
            overhead_costs=Decimal(model.overhead_costs),
            timeline_event_costs={k: Decimal(v) for k, v in model.get_timeline_event_costs().items()},
            total_cost=Decimal(model.total_cost)
        )


class SQLOfferRepository(BaseRepository[OfferModel]):
    """SQLAlchemy implementation of OfferRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(OfferModel, db)

    def save(self, offer: Offer) -> Offer:
        """Save an offer."""
        model = OfferModel(
            id=str(offer.id),
            route_id=str(offer.route_id),
            cost_breakdown_id=str(offer.cost_breakdown_id),
            margin_percentage=str(offer.margin_percentage),
            final_price=str(offer.final_price),
            ai_content=offer.ai_content,
            fun_fact=offer.fun_fact,
            created_at=offer.created_at
        )
        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Offer]:
        """Find an offer by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: OfferModel) -> Offer:
        """Convert model to domain entity."""
        return Offer(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            cost_breakdown_id=UUID(model.cost_breakdown_id),
            margin_percentage=Decimal(model.margin_percentage),
            final_price=Decimal(model.final_price),
            ai_content=model.ai_content,
            fun_fact=model.fun_fact,
            created_at=model.created_at
        ) 