"""SQLAlchemy models for cargo and cost-related entities."""
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, ForeignKey, JSON,
    DateTime
)
from sqlalchemy.orm import relationship

from ..database import Base


class CargoModel(Base):
    """SQLAlchemy model for cargo."""
    __tablename__ = "cargos"

    id = Column(String(36), primary_key=True)
    weight = Column(Float, nullable=False)
    value = Column(String(50), nullable=False)  # Stored as string for Decimal
    special_requirements = Column(JSON, nullable=False)

    def get_special_requirements(self) -> list[str]:
        """Get special requirements as list."""
        return json.loads(self.special_requirements)

    def set_special_requirements(self, requirements: list[str]):
        """Set special requirements from list."""
        self.special_requirements = json.dumps(requirements)


class CostSettingsModel(Base):
    """SQLAlchemy model for cost settings."""
    __tablename__ = "cost_settings"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id"))
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"))
    enabled_components = Column(JSON, nullable=False)
    rates = Column(JSON, nullable=False)  # Stored as JSON string of decimal values

    def get_enabled_components(self) -> list[str]:
        """Get enabled components as list."""
        return json.loads(self.enabled_components)

    def set_enabled_components(self, components: list[str]):
        """Set enabled components from list."""
        self.enabled_components = json.dumps(components)

    def get_rates(self) -> dict[str, str]:
        """Get rates as dictionary with decimal strings."""
        return json.loads(self.rates)

    def set_rates(self, rates: dict[str, str]):
        """Set rates from dictionary with decimal strings."""
        self.rates = json.dumps(rates)


class CostBreakdownModel(Base):
    """SQLAlchemy model for cost breakdowns."""
    __tablename__ = "cost_breakdowns"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id"))
    fuel_costs = Column(JSON, nullable=False)  # Per country
    toll_costs = Column(JSON, nullable=False)  # Per country
    driver_costs = Column(String(50), nullable=False)  # Stored as string for Decimal
    overhead_costs = Column(String(50), nullable=False)  # Stored as string for Decimal
    timeline_event_costs = Column(JSON, nullable=False)
    total_cost = Column(String(50), nullable=False)  # Stored as string for Decimal

    def get_fuel_costs(self) -> dict[str, str]:
        """Get fuel costs as dictionary with decimal strings."""
        return json.loads(self.fuel_costs)

    def set_fuel_costs(self, costs: dict[str, str]):
        """Set fuel costs from dictionary with decimal strings."""
        self.fuel_costs = json.dumps(costs)

    def get_toll_costs(self) -> dict[str, str]:
        """Get toll costs as dictionary with decimal strings."""
        return json.loads(self.toll_costs)

    def set_toll_costs(self, costs: dict[str, str]):
        """Set toll costs from dictionary with decimal strings."""
        self.toll_costs = json.dumps(costs)

    def get_timeline_event_costs(self) -> dict[str, str]:
        """Get timeline event costs as dictionary with decimal strings."""
        return json.loads(self.timeline_event_costs)

    def set_timeline_event_costs(self, costs: dict[str, str]):
        """Set timeline event costs from dictionary with decimal strings."""
        self.timeline_event_costs = json.dumps(costs)


class OfferModel(Base):
    """SQLAlchemy model for offers."""
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id"))
    cost_breakdown_id = Column(String(36), ForeignKey("cost_breakdowns.id"))
    margin_percentage = Column(String(50), nullable=False)  # Stored as string for Decimal
    final_price = Column(String(50), nullable=False)  # Stored as string for Decimal
    ai_content = Column(String(1000), nullable=True)
    fun_fact = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    cost_breakdown = relationship("CostBreakdownModel") 