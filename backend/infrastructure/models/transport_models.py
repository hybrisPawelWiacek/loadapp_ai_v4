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


class DriverSpecificationModel(Base):
    """SQLAlchemy model for driver specifications."""
    __tablename__ = "driver_specifications"

    id = Column(String(36), primary_key=True)
    daily_rate = Column(String(50), nullable=False)  # Stored as string for Decimal
    required_license_type = Column(String(50), nullable=False)
    required_certifications = Column(String(500), nullable=False)  # Stored as JSON string

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