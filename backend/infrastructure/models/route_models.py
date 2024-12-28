"""SQLAlchemy models for route-related entities."""
from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey,
    DateTime, Integer, JSON
)
from sqlalchemy.orm import relationship

from ..database import Base


class LocationModel(Base):
    """SQLAlchemy model for locations."""
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=False)


class EmptyDrivingModel(Base):
    """SQLAlchemy model for empty driving segments."""
    __tablename__ = "empty_drivings"

    id = Column(String(36), primary_key=True)
    distance_km = Column(Float, default=200.0)
    duration_hours = Column(Float, default=4.0)


class TimelineEventModel(Base):
    """SQLAlchemy model for timeline events."""
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id"))
    type = Column(String(50), nullable=False)  # pickup/rest/delivery
    location_id = Column(String(36), ForeignKey("locations.id"))
    planned_time = Column(DateTime(timezone=True), nullable=False)
    duration_hours = Column(Float, default=1.0)
    event_order = Column(Integer, nullable=False)

    # Relationships
    location = relationship("LocationModel")


class CountrySegmentModel(Base):
    """SQLAlchemy model for country segments."""
    __tablename__ = "country_segments"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id"))
    country_code = Column(String(2), nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)
    start_location_id = Column(String(36), ForeignKey("locations.id"))
    end_location_id = Column(String(36), ForeignKey("locations.id"))

    # Relationships
    start_location = relationship("LocationModel", foreign_keys=[start_location_id])
    end_location = relationship("LocationModel", foreign_keys=[end_location_id])


class RouteModel(Base):
    """SQLAlchemy model for routes."""
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True)
    transport_id = Column(String(36), ForeignKey("transports.id"))
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"))
    cargo_id = Column(String(36), ForeignKey("cargos.id"))
    origin_id = Column(String(36), ForeignKey("locations.id"))
    destination_id = Column(String(36), ForeignKey("locations.id"))
    pickup_time = Column(DateTime(timezone=True), nullable=False)
    delivery_time = Column(DateTime(timezone=True), nullable=False)
    empty_driving_id = Column(String(36), ForeignKey("empty_drivings.id"))
    total_distance_km = Column(Float, nullable=False)
    total_duration_hours = Column(Float, nullable=False)
    is_feasible = Column(Boolean, default=True)

    # Relationships
    origin = relationship("LocationModel", foreign_keys=[origin_id])
    destination = relationship("LocationModel", foreign_keys=[destination_id])
    empty_driving = relationship("EmptyDrivingModel")
    timeline_events = relationship("TimelineEventModel", 
                                 order_by="TimelineEventModel.event_order",
                                 cascade="all, delete-orphan")
    country_segments = relationship("CountrySegmentModel",
                                  cascade="all, delete-orphan") 