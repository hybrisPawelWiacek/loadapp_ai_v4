"""SQLAlchemy models for transport-related entities."""
from decimal import Decimal
import json
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database import Base


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
    required_license_type = Column(String(50), nullable=False)
    required_certifications = Column(String(500), nullable=False)  # Stored as JSON string

    def __init__(self, id, daily_rate, required_license_type, required_certifications):
        self.id = id
        self.daily_rate = daily_rate
        self.required_license_type = required_license_type
        self.required_certifications = required_certifications

    def get_certifications(self) -> list[str]:
        """Get certifications as list."""
        return json.loads(self.required_certifications) if self.required_certifications else []

    def set_certifications(self, certifications: list[str]):
        """Set certifications from list."""
        self.required_certifications = json.dumps(certifications) if certifications else "[]"


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
    transport_type_id = Column(String(50), ForeignKey("transport_types.id"))
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"))
    truck_specifications_id = Column(String(36), ForeignKey("truck_specifications.id"))
    driver_specifications_id = Column(String(36), ForeignKey("driver_specifications.id"))
    is_active = Column(Boolean, default=True)

    # Relationships
    transport_type = relationship("TransportTypeModel")
    truck_specifications = relationship("TruckSpecificationModel")
    driver_specifications = relationship("DriverSpecificationModel")
    business_entity = relationship("BusinessEntityModel", back_populates="transports")

    def __init__(self, id, transport_type_id=None, business_entity_id=None,
                 truck_specifications_id=None, driver_specifications_id=None, is_active=True):
        self.id = id
        self.transport_type_id = transport_type_id
        self.business_entity_id = business_entity_id
        self.truck_specifications_id = truck_specifications_id
        self.driver_specifications_id = driver_specifications_id
        self.is_active = is_active 