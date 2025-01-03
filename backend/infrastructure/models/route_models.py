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
    latitude = Column(String(50), nullable=False)  # Store as string for Decimal
    longitude = Column(String(50), nullable=False)  # Store as string for Decimal
    address = Column(String(500), nullable=False)

    def __init__(self, id, latitude, longitude, address):
        self.id = id
        self.latitude = str(latitude)  # Convert to string
        self.longitude = str(longitude)  # Convert to string
        self.address = address


class EmptyDrivingModel(Base):
    """SQLAlchemy model for empty driving segments."""
    __tablename__ = "empty_drivings"

    id = Column(String(36), primary_key=True)
    distance_km = Column(String(50), nullable=False)  # Store as string for Decimal
    duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal

    def __init__(self, id, distance_km, duration_hours):
        self.id = id
        self.distance_km = str(distance_km)  # Convert to string
        self.duration_hours = str(duration_hours)  # Convert to string


class TimelineEventModel(Base):
    """SQLAlchemy model for timeline events."""
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # pickup/rest/delivery
    location_id = Column(String(36), ForeignKey("locations.id"))
    planned_time = Column(DateTime(timezone=True), nullable=False)
    duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal
    event_order = Column(Integer, nullable=False)

    # Relationships
    location = relationship("LocationModel")

    def __init__(self, id, route_id, type, location_id, planned_time, duration_hours=1.0, event_order=None):
        self.id = id
        self.route_id = route_id
        self.type = type
        self.location_id = location_id
        # Ensure timezone info is preserved
        if planned_time.tzinfo is None:
            from datetime import timezone
            planned_time = planned_time.replace(tzinfo=timezone.utc)
        self.planned_time = planned_time
        self.duration_hours = str(duration_hours)  # Convert to string
        self.event_order = event_order


class CountrySegmentModel(Base):
    """SQLAlchemy model for country segments."""
    __tablename__ = "country_segments"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=True)
    country_code = Column(String(2), nullable=False)
    distance_km = Column(String(50), nullable=False)  # Store as string for Decimal
    duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal
    start_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    end_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    segment_order = Column(Integer, nullable=False)  # Add segment order field

    # Relationships
    start_location = relationship("LocationModel", foreign_keys=[start_location_id])
    end_location = relationship("LocationModel", foreign_keys=[end_location_id])
    route = relationship("RouteModel", back_populates="country_segments", foreign_keys=[route_id])

    def __init__(self, id, route_id, country_code, distance_km, duration_hours, start_location_id, end_location_id, segment_order=0):
        self.id = id
        self.route_id = route_id
        self.country_code = country_code
        self.distance_km = str(distance_km)  # Convert to string
        self.duration_hours = str(duration_hours)  # Convert to string
        self.start_location_id = start_location_id
        self.end_location_id = end_location_id
        self.segment_order = segment_order


class RouteModel(Base):
    """SQLAlchemy model for routes."""
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True)
    transport_id = Column(String(36), ForeignKey("transports.id"), nullable=False)
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"), nullable=False)
    cargo_id = Column(String(36), ForeignKey("cargos.id"))
    origin_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    destination_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    pickup_time = Column(DateTime(timezone=True), nullable=False)
    delivery_time = Column(DateTime(timezone=True), nullable=False)
    empty_driving_id = Column(String(36), ForeignKey("empty_drivings.id"))
    total_distance_km = Column(String(50), nullable=False)  # Store as string for Decimal
    total_duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal
    is_feasible = Column(Boolean, default=True)
    status = Column(String(50), default="draft")

    # Add validation fields
    certifications_validated = Column(Boolean, default=False)
    operating_countries_validated = Column(Boolean, default=False)
    validation_timestamp = Column(DateTime(timezone=True), nullable=True)
    validation_details = Column(JSON, nullable=True)  # For storing additional validation info

    # Relationships
    transport = relationship("TransportModel")
    business_entity = relationship("BusinessEntityModel")
    cargo = relationship("CargoModel")
    origin = relationship("LocationModel", foreign_keys=[origin_id])
    destination = relationship("LocationModel", foreign_keys=[destination_id])
    empty_driving = relationship("EmptyDrivingModel")
    timeline_events = relationship("TimelineEventModel", cascade="all, delete-orphan", backref="route", lazy="joined")
    country_segments = relationship("CountrySegmentModel", cascade="all, delete-orphan", back_populates="route", lazy="joined")

    def __init__(self, id, transport_id, business_entity_id,
                 origin_id, destination_id, pickup_time, delivery_time,
                 total_distance_km, total_duration_hours,
                 cargo_id=None, empty_driving_id=None,
                 is_feasible=True, status="draft",
                 timeline_events=None, country_segments=None):
        self.id = id
        self.transport_id = transport_id
        self.business_entity_id = business_entity_id
        self.cargo_id = cargo_id
        self.origin_id = origin_id
        self.destination_id = destination_id
        # Ensure timezone info is preserved
        if pickup_time.tzinfo is None:
            from datetime import timezone
            pickup_time = pickup_time.replace(tzinfo=timezone.utc)
        if delivery_time.tzinfo is None:
            from datetime import timezone
            delivery_time = delivery_time.replace(tzinfo=timezone.utc)
        self.pickup_time = pickup_time
        self.delivery_time = delivery_time
        self.empty_driving_id = empty_driving_id
        self.total_distance_km = str(total_distance_km)  # Convert to string
        self.total_duration_hours = str(total_duration_hours)  # Convert to string
        self.is_feasible = is_feasible
        self.status = status
        self.timeline_events = timeline_events or []
        self.country_segments = country_segments or [] 