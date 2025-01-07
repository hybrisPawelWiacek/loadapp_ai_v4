"""SQLAlchemy models for transport-related entities."""
from decimal import Decimal
import json
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, UUID, Numeric, DateTime, text
from sqlalchemy.orm import relationship
from uuid import uuid4

from ..database import Base
from .business_models import BusinessEntityModel


class TruckSpecificationModel(Base):
    """SQLAlchemy model for truck specifications."""
    __tablename__ = "truck_specifications"

    id = Column(String(36), primary_key=True)
    fuel_consumption_empty = Column(Float, nullable=False)
    fuel_consumption_loaded = Column(Float, nullable=False)
    toll_class = Column(String(50), nullable=False)
    euro_class = Column(String(50), nullable=False)
    co2_class = Column(String(50), nullable=False)
    maintenance_rate_per_km = Column(String(50), nullable=False)  # Stored as string for Decimal

    def __init__(self, id, fuel_consumption_empty, fuel_consumption_loaded, toll_class, euro_class, co2_class, maintenance_rate_per_km):
        self.id = id
        self.fuel_consumption_empty = fuel_consumption_empty
        self.fuel_consumption_loaded = fuel_consumption_loaded
        self.toll_class = toll_class
        self.euro_class = euro_class
        self.co2_class = co2_class
        self.maintenance_rate_per_km = maintenance_rate_per_km


class DriverSpecificationModel(Base):
    """SQLAlchemy model for driver specifications."""
    __tablename__ = "driver_specifications"

    id = Column(String(36), primary_key=True)
    daily_rate = Column(String(50), nullable=False)  # Stored as string for Decimal
    driving_time_rate = Column(String(50), nullable=False)  # Stored as string for Decimal
    required_license_type = Column(String(50), nullable=False)
    required_certifications = Column(String(500), nullable=False)  # Stored as JSON string
    max_driving_hours = Column(String(50), nullable=False, default="9")  # Default 9 hours
    overtime_rate_multiplier = Column(String(50), nullable=False, default="1.5")  # Default 1.5x

    def __init__(self, id, daily_rate, driving_time_rate, required_license_type, required_certifications,
                 max_driving_hours="9", overtime_rate_multiplier="1.5"):
        self.id = id
        self.daily_rate = daily_rate
        self.driving_time_rate = driving_time_rate
        self.required_license_type = required_license_type
        self.set_certifications(required_certifications)
        self.max_driving_hours = max_driving_hours
        self.overtime_rate_multiplier = overtime_rate_multiplier

    def get_certifications(self) -> list[str]:
        """Get certifications as list."""
        try:
            # If it's already a JSON string, parse it
            if isinstance(self.required_certifications, str):
                return json.loads(self.required_certifications)
            # If it's already a list, return it
            elif isinstance(self.required_certifications, list):
                return self.required_certifications
            # Default to empty list
            return []
        except json.JSONDecodeError:
            # If JSON parsing fails, return as is (assuming it's already a list)
            return self.required_certifications

    def set_certifications(self, certifications: list[str]):
        """Set certifications from list."""
        # If it's already a JSON string, store it as is
        if isinstance(certifications, str):
            try:
                # Validate it's a proper JSON string
                json.loads(certifications)
                self.required_certifications = certifications
            except json.JSONDecodeError:
                # If not valid JSON, convert to JSON
                self.required_certifications = json.dumps(certifications)
        # If it's a list, convert to JSON string
        elif isinstance(certifications, list):
            self.required_certifications = json.dumps(certifications)
        # Default to empty list
        else:
            self.required_certifications = "[]"


class TransportTypeModel(Base):
    """SQLAlchemy model for transport types."""
    __tablename__ = "transport_types"

    id = Column(String(50), primary_key=True)  # flatbed/container etc.
    name = Column(String(100), nullable=False)
    truck_specifications_id = Column(String(36), ForeignKey("truck_specifications.id"))
    driver_specifications_id = Column(String(36), ForeignKey("driver_specifications.id"))

    # Relationships
    truck_specifications = relationship("TruckSpecificationModel")
    driver_specifications = relationship("DriverSpecificationModel")

    def __init__(self, id, name, truck_specifications_id=None, driver_specifications_id=None,
                 truck_specifications=None, driver_specifications=None):
        self.id = id
        self.name = name
        if truck_specifications:
            self.truck_specifications = truck_specifications
            self.truck_specifications_id = truck_specifications.id
        else:
            self.truck_specifications_id = truck_specifications_id
            
        if driver_specifications:
            self.driver_specifications = driver_specifications
            self.driver_specifications_id = driver_specifications.id
        else:
            self.driver_specifications_id = driver_specifications_id


class TransportModel(Base):
    """SQLAlchemy model for transport instances."""
    __tablename__ = "transports"

    id = Column(String(36), primary_key=True)
    transport_type_id = Column(String(50), ForeignKey("transport_types.id"), nullable=False)
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"), nullable=False)
    truck_specifications_id = Column(String(36), ForeignKey("truck_specifications.id"), nullable=False)
    driver_specifications_id = Column(String(36), ForeignKey("driver_specifications.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    transport_type = relationship("TransportTypeModel")
    truck_specifications = relationship("TruckSpecificationModel")
    driver_specifications = relationship("DriverSpecificationModel")
    business_entity = relationship("BusinessEntityModel", back_populates="transports")
    routes = relationship("RouteModel", backref="transport", lazy="dynamic", cascade="all, delete-orphan")

    def __init__(self, id, transport_type_id=None, business_entity_id=None,
                 truck_specifications_id=None, driver_specifications_id=None, is_active=True):
        self.id = id
        self.transport_type_id = transport_type_id
        self.business_entity_id = business_entity_id
        self.truck_specifications_id = truck_specifications_id
        self.driver_specifications_id = driver_specifications_id
        self.is_active = is_active 


class TollRateOverrideModel(Base):
    """SQLAlchemy model for toll rate overrides."""
    __tablename__ = 'toll_rate_overrides'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    vehicle_class = Column(String(50), nullable=False)
    rate_multiplier = Column(Numeric(3, 2), nullable=False)
    country_code = Column(String(2), nullable=False)
    route_type = Column(String(50))
    business_entity_id = Column(String(36), ForeignKey('business_entities.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), onupdate=text('CURRENT_TIMESTAMP'))

    # Relationships
    business_entity = relationship('BusinessEntityModel', back_populates='toll_rate_overrides')

    def __repr__(self):
        return (f"<TollRateOverride(id={self.id}, "
                f"country_code={self.country_code}, "
                f"vehicle_class={self.vehicle_class}, "
                f"rate_multiplier={self.rate_multiplier})>")

# Update BusinessEntityModel to include the relationship
BusinessEntityModel.toll_rate_overrides = relationship(
    'TollRateOverrideModel',
    back_populates='business_entity',
    cascade='all, delete-orphan'
) 