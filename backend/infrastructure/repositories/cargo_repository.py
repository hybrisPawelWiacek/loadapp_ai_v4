"""Repository implementations for cargo and cost-related entities."""
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...domain.entities.cargo import (
    Cargo, CostSettings, CostSettingsCreate,
    CostBreakdown, Offer
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
        existing_model = self.get(str(cargo.id))
        if existing_model:
            # Update existing cargo
            existing_model.business_entity_id = str(cargo.business_entity_id) if cargo.business_entity_id else None
            existing_model.weight = cargo.weight
            existing_model.volume = cargo.volume
            existing_model.cargo_type = cargo.cargo_type
            existing_model.value = str(cargo.value)
            existing_model.special_requirements = cargo.special_requirements
            existing_model.status = cargo.status
            return self._to_domain(self.update(existing_model))
        else:
            # Create new cargo
            model = CargoModel(
                id=str(cargo.id),
                business_entity_id=str(cargo.business_entity_id) if cargo.business_entity_id else None,
                weight=cargo.weight,
                volume=cargo.volume,
                cargo_type=cargo.cargo_type,
                value=str(cargo.value),
                special_requirements=cargo.special_requirements,
                status=cargo.status
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
            business_entity_id=UUID(model.business_entity_id) if model.business_entity_id else None,
            weight=model.weight,
            volume=model.volume,
            cargo_type=model.cargo_type,
            value=Decimal(model.value),
            special_requirements=model.get_special_requirements(),
            status=model.status
        )


class SQLCostSettingsRepository(BaseRepository[CostSettingsModel]):
    """SQLAlchemy implementation of CostSettingsRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(CostSettingsModel, db)

    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings."""
        # Check if settings already exist
        existing = self.get(str(settings.id))
        if existing:
            # Update existing model
            existing.route_id = str(settings.route_id)
            existing.business_entity_id = str(settings.business_entity_id)
            existing.set_enabled_components(settings.enabled_components)
            existing.set_rates({k: str(v) for k, v in settings.rates.items()})
            return self._to_domain(self.update(existing))
        else:
            # Create new model
            model = CostSettingsModel(
                id=str(settings.id),
                route_id=str(settings.route_id),
                business_entity_id=str(settings.business_entity_id)
            )
            model.set_enabled_components(settings.enabled_components)
            model.set_rates({k: str(v) for k, v in settings.rates.items()})
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

    def create_settings(
        self,
        route_id: UUID,
        settings: CostSettingsCreate,
        business_entity_id: UUID
    ) -> CostSettings:
        """Create new cost settings."""
        model = CostSettingsModel(
            id=str(uuid4()),
            route_id=str(route_id),
            business_entity_id=str(business_entity_id)
        )
        model.set_enabled_components(settings.enabled_components)
        model.set_rates({k: str(v) for k, v in settings.rates.items()})
        return self._to_domain(super().create(model))


class SQLCostBreakdownRepository(BaseRepository[CostBreakdownModel]):
    """SQLAlchemy implementation of CostBreakdownRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(CostBreakdownModel, db)

    def save(self, breakdown: CostBreakdown) -> CostBreakdown:
        """Save cost breakdown."""
        model = CostBreakdownModel(
            id=str(breakdown.id),
            route_id=str(breakdown.route_id)
        )
        model.set_fuel_costs({k: str(v) for k, v in breakdown.fuel_costs.items()})
        model.set_toll_costs({k: str(v) for k, v in breakdown.toll_costs.items()})
        model.driver_costs = str(breakdown.driver_costs)
        model.overhead_costs = str(breakdown.overhead_costs)
        model.set_timeline_event_costs({k: str(v) for k, v in breakdown.timeline_event_costs.items()})
        model.total_cost = str(breakdown.total_cost)
        return self._to_domain(self.create(model))

    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find cost breakdown by route ID."""
        model = self.list(route_id=str(route_id))[0] if self.list(route_id=str(route_id)) else None
        return self._to_domain(model) if model else None

    def _to_domain(self, model: CostBreakdownModel) -> CostBreakdown:
        """Convert model to domain entity."""
        return CostBreakdown(
            id=UUID(model.id),
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
        # Check if offer already exists
        existing = self.get(str(offer.id))
        if existing:
            # Update existing model
            existing.route_id = str(offer.route_id)
            existing.cost_breakdown_id = str(offer.cost_breakdown_id)
            existing.margin_percentage = str(offer.margin_percentage)
            existing.final_price = str(offer.final_price)
            existing.ai_content = offer.ai_content
            existing.fun_fact = offer.fun_fact
            existing.status = offer.status
            # Keep the original timestamps
            existing.created_at = offer.created_at
            existing.finalized_at = offer.finalized_at
            return self._to_domain(self.update(existing))
        else:
            # Create new model
            model = OfferModel(
                id=str(offer.id),
                route_id=str(offer.route_id),
                cost_breakdown_id=str(offer.cost_breakdown_id),
                margin_percentage=str(offer.margin_percentage),
                final_price=str(offer.final_price),
                ai_content=offer.ai_content,
                fun_fact=offer.fun_fact,
                status=offer.status,
                # Keep the original timestamps
                created_at=offer.created_at,
                finalized_at=offer.finalized_at
            )
            return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Offer]:
        """Find an offer by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def find_model_by_id(self, id: UUID) -> Optional[OfferModel]:
        """Find an offer model by ID."""
        return self.get(str(id))

    def _to_domain(self, model: OfferModel) -> Optional[Offer]:
        """Convert model to domain entity."""
        if not model:
            return None
        return Offer(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            cost_breakdown_id=UUID(model.cost_breakdown_id),
            margin_percentage=Decimal(model.margin_percentage),
            final_price=Decimal(model.final_price),
            ai_content=model.ai_content,
            fun_fact=model.fun_fact,
            created_at=model.created_at,
            finalized_at=model.finalized_at,
            status=model.status
        ) 