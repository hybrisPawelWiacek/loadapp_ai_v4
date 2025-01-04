"""SQLAlchemy models for cargo and cost-related entities."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, String, Float, ForeignKey, JSON,
    DateTime, Boolean
)
from sqlalchemy.orm import relationship

from ..database import Base


class CargoModel(Base):
    """SQLAlchemy model for cargo."""
    __tablename__ = "cargos"

    id = Column(String(36), primary_key=True)
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"))
    weight = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)
    cargo_type = Column(String(50), nullable=False, default='general')
    value = Column(String(50), nullable=False)  # Stored as string for Decimal
    special_requirements = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships with deferred loading
    business_entity = relationship("BusinessEntityModel", back_populates="cargos", lazy="joined", post_update=True)
    status_history = relationship("CargoStatusHistoryModel", back_populates="cargo", lazy="dynamic", cascade="all, delete-orphan")
    routes = relationship("RouteModel", back_populates="cargo", lazy="dynamic", cascade="all, delete-orphan")

    def __init__(self, id, business_entity_id=None, weight=None, volume=None, 
                 cargo_type=None, value=None, special_requirements=None, status='pending'):
        if weight is None:
            raise ValueError("weight is required")
        if value is None:
            raise ValueError("value is required")
        if special_requirements is None:
            raise ValueError("special_requirements is required")

        self.id = id
        self.business_entity_id = business_entity_id
        self.weight = weight
        self.volume = volume or 0.0
        self.cargo_type = cargo_type or 'general'
        self.value = str(value) if isinstance(value, (Decimal, float)) else value
        self.special_requirements = special_requirements if isinstance(special_requirements, str) else json.dumps(special_requirements)
        self.status = status
        self.created_at = datetime.utcnow()
        self.updated_at = None
        self.is_active = True

    def update(self, **kwargs):
        """Update cargo attributes and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'special_requirements' and not isinstance(value, str):
                    value = json.dumps(value)
                elif key == 'value' and isinstance(value, (Decimal, float)):
                    value = str(value)
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def get_special_requirements(self) -> list[str]:
        """Get special requirements as list."""
        if not self.special_requirements:
            return []
        if isinstance(self.special_requirements, list):
            return self.special_requirements
        return json.loads(self.special_requirements)

    def set_special_requirements(self, requirements: list[str]):
        """Set special requirements from list."""
        self.special_requirements = requirements if isinstance(requirements, str) else json.dumps(requirements)
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'business_entity_id': self.business_entity_id,
            'weight': self.weight,
            'volume': self.volume,
            'cargo_type': self.cargo_type,
            'value': self.value,
            'special_requirements': self.get_special_requirements(),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


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

    def __init__(self, id, route_id, fuel_costs=None, toll_costs=None,
                 driver_costs=None, overhead_costs=None, timeline_event_costs=None,
                 total_cost=None):
        self.id = id
        self.route_id = route_id
        self.set_fuel_costs(fuel_costs or {})
        self.set_toll_costs(toll_costs or {})
        self.driver_costs = str(driver_costs) if driver_costs is not None else "0"
        self.overhead_costs = str(overhead_costs) if overhead_costs is not None else "0"
        self.set_timeline_event_costs(timeline_event_costs or {})
        self.total_cost = str(total_cost) if total_cost is not None else "0"

    def get_fuel_costs(self) -> dict[str, str]:
        """Get fuel costs as dictionary with decimal strings."""
        if isinstance(self.fuel_costs, str):
            return json.loads(self.fuel_costs)
        return self.fuel_costs or {}

    def set_fuel_costs(self, costs: dict[str, str | Decimal | float]):
        """Set fuel costs from dictionary with decimal strings."""
        if isinstance(costs, str):
            self.fuel_costs = costs
        else:
            # Convert all values to strings
            costs_str = {k: str(v) if isinstance(v, (Decimal, float)) else v for k, v in costs.items()}
            self.fuel_costs = json.dumps(costs_str) if costs else "{}"

    def get_toll_costs(self) -> dict[str, str]:
        """Get toll costs as dictionary with decimal strings."""
        if isinstance(self.toll_costs, str):
            return json.loads(self.toll_costs)
        return self.toll_costs or {}

    def set_toll_costs(self, costs: dict[str, str | Decimal | float]):
        """Set toll costs from dictionary with decimal strings."""
        if isinstance(costs, str):
            self.toll_costs = costs
        else:
            # Convert all values to strings
            costs_str = {k: str(v) if isinstance(v, (Decimal, float)) else v for k, v in costs.items()}
            self.toll_costs = json.dumps(costs_str) if costs else "{}"

    def get_timeline_event_costs(self) -> dict[str, str]:
        """Get timeline event costs as dictionary with decimal strings."""
        if isinstance(self.timeline_event_costs, str):
            return json.loads(self.timeline_event_costs)
        return self.timeline_event_costs or {}

    def set_timeline_event_costs(self, costs: dict[str, str | Decimal | float]):
        """Set timeline event costs from dictionary with decimal strings."""
        if isinstance(costs, str):
            self.timeline_event_costs = costs
        else:
            # Convert all values to strings
            costs_str = {k: str(v) if isinstance(v, (Decimal, float)) else v for k, v in costs.items()}
            self.timeline_event_costs = json.dumps(costs_str) if costs else "{}"


class OfferModel(Base):
    """SQLAlchemy model for offers."""
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True)
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"))
    route_id = Column(String(36), ForeignKey("routes.id"))
    cost_breakdown_id = Column(String(36), ForeignKey("cost_breakdowns.id"))
    margin_percentage = Column(String(50), nullable=False)  # Stored as string for Decimal
    final_price = Column(String(50), nullable=False)  # Stored as string for Decimal
    ai_content = Column(String(1000), nullable=True)
    fun_fact = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="draft")

    # Relationships
    business_entity = relationship("BusinessEntityModel", back_populates="offers")
    cost_breakdown = relationship("CostBreakdownModel")
    status_history = relationship("OfferStatusHistoryModel", back_populates="offer", lazy="dynamic", cascade="all, delete-orphan")

    def __init__(self, id, route_id, cost_breakdown_id, margin_percentage, final_price,
                 ai_content=None, fun_fact=None, created_at=None, finalized_at=None, status="draft"):
        self.id = id
        self.route_id = route_id
        self.cost_breakdown_id = cost_breakdown_id
        self.margin_percentage = str(margin_percentage) if isinstance(margin_percentage, (Decimal, float)) else margin_percentage
        self.final_price = str(final_price) if isinstance(final_price, (Decimal, float)) else final_price
        self.ai_content = ai_content
        self.fun_fact = fun_fact
        self.status = status
        # Store timestamp in UTC
        if created_at is not None:
            # If the timestamp has no timezone info, assume it's UTC
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            # Convert to UTC if it's not already
            if created_at.tzinfo != timezone.utc:
                created_at = created_at.astimezone(timezone.utc)
            self.created_at = created_at
        else:
            self.created_at = datetime.now(timezone.utc)
            
        # Handle finalized_at timestamp
        if finalized_at is not None:
            # If the timestamp has no timezone info, assume it's UTC
            if finalized_at.tzinfo is None:
                finalized_at = finalized_at.replace(tzinfo=timezone.utc)
            # Convert to UTC if it's not already
            if finalized_at.tzinfo != timezone.utc:
                finalized_at = finalized_at.astimezone(timezone.utc)
            self.finalized_at = finalized_at
        else:
            self.finalized_at = None

    def to_dict(self):
        """Convert offer to dictionary."""
        return {
            "id": self.id,
            "route_id": self.route_id,
            "cost_breakdown_id": self.cost_breakdown_id,
            "margin_percentage": self.margin_percentage,
            "final_price": self.final_price,
            "ai_content": self.ai_content,
            "fun_fact": self.fun_fact,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finalized_at": self.finalized_at.isoformat() if self.finalized_at else None,
            "status": self.status
        } 


class CargoStatusHistoryModel(Base):
    """SQLAlchemy model for cargo status history."""
    __tablename__ = "cargo_status_history"

    id = Column(String(36), primary_key=True)
    cargo_id = Column(String(36), ForeignKey("cargos.id"), nullable=False)
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    trigger = Column(String(50), nullable=False)  # e.g., 'offer_finalization', 'manual_update', etc.
    trigger_id = Column(String(36), nullable=True)  # e.g., offer_id for offer finalization
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    details = Column(JSON, nullable=True)  # Additional context about the status change

    # Relationship
    cargo = relationship("CargoModel", back_populates="status_history")

    def __init__(self, id, cargo_id, old_status, new_status, trigger, trigger_id=None, details=None):
        self.id = id
        self.cargo_id = cargo_id
        self.old_status = old_status
        self.new_status = new_status
        self.trigger = trigger
        self.trigger_id = trigger_id
        self.timestamp = datetime.now(timezone.utc)
        self.details = json.dumps(details) if details else None

    def to_dict(self):
        """Convert status history entry to dictionary."""
        return {
            "id": self.id,
            "cargo_id": self.cargo_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "trigger": self.trigger,
            "trigger_id": self.trigger_id,
            "timestamp": self.timestamp.isoformat(),
            "details": json.loads(self.details) if self.details else None
        } 


class OfferStatusHistoryModel(Base):
    """SQLAlchemy model for offer status history."""
    __tablename__ = "offer_status_history"

    id = Column(String(36), primary_key=True)
    offer_id = Column(String(36), ForeignKey("offers.id"), nullable=False)
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    trigger = Column(String(50), nullable=False)  # e.g., 'manual_update', 'system_update', etc.
    trigger_id = Column(String(36), nullable=True)  # e.g., user_id for manual updates
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    details = Column(JSON, nullable=True)  # Additional context about the status change

    # Relationship
    offer = relationship("OfferModel", back_populates="status_history")

    def __init__(self, id, offer_id, old_status, new_status, trigger, trigger_id=None, details=None):
        self.id = id
        self.offer_id = offer_id
        self.old_status = old_status
        self.new_status = new_status
        self.trigger = trigger
        self.trigger_id = trigger_id
        self.timestamp = datetime.utcnow()
        self.details = json.dumps(details) if details else None

    def get_details(self) -> dict:
        """Get details as dictionary."""
        if not self.details:
            return {}
        if isinstance(self.details, dict):
            return self.details
        return json.loads(self.details)

    def to_dict(self):
        """Convert status history entry to dictionary."""
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'trigger': self.trigger,
            'trigger_id': self.trigger_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'details': self.get_details()
        } 