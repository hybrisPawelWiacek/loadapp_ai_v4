"""SQLAlchemy models for route-related entities."""
from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey,
    DateTime, Integer, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
import json
from datetime import datetime, timezone
from typing import Optional

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

    def to_dict(self):
        """Convert timeline event to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "route_id": str(self.route_id),
            "type": self.type,
            "location_id": str(self.location_id),
            "planned_time": self.planned_time.isoformat(),
            "duration_hours": float(self.duration_hours),
            "event_order": self.event_order
        }


class CountrySegmentModel(Base):
    """SQLAlchemy model for country segments."""
    __tablename__ = "country_segments"

    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    country_code = Column(String(2), nullable=False)
    distance_km = Column(String(50), nullable=False)  # Store as string for Decimal
    duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal
    start_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    end_location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    segment_order = Column(Integer, nullable=False)

    # Relationships
    start_location = relationship("LocationModel", foreign_keys=[start_location_id])
    end_location = relationship("LocationModel", foreign_keys=[end_location_id])

    def __init__(self, id, route_id, country_code, distance_km, duration_hours,
                 start_location_id, end_location_id, segment_order):
        self.id = id
        self.route_id = route_id
        self.country_code = country_code
        self.distance_km = str(distance_km)  # Convert to string
        self.duration_hours = str(duration_hours)  # Convert to string
        self.start_location_id = start_location_id
        self.end_location_id = end_location_id
        self.segment_order = segment_order

    def to_dict(self):
        """Convert country segment to dictionary."""
        return {
            'id': str(self.id),
            'route_id': str(self.route_id),
            'country_code': self.country_code,
            'distance_km': float(self.distance_km),
            'duration_hours': float(self.duration_hours),
            'start_location_id': str(self.start_location_id),
            'end_location_id': str(self.end_location_id),
            'segment_order': self.segment_order
        }


class RouteModel(Base):
    """SQLAlchemy model for routes."""
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True)
    transport_id = Column(String(36), ForeignKey("transports.id"), nullable=False)
    business_entity_id = Column(String(36), ForeignKey("business_entities.id"), nullable=False)
    cargo_id = Column(String(36), ForeignKey("cargos.id"), nullable=True)
    origin_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    destination_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    pickup_time = Column(DateTime(timezone=True), nullable=False)
    delivery_time = Column(DateTime(timezone=True), nullable=False)
    empty_driving_id = Column(String(36), ForeignKey("empty_drivings.id"), nullable=True)
    total_distance_km = Column(String(50), nullable=False)  # Store as string for Decimal
    total_duration_hours = Column(String(50), nullable=False)  # Store as string for Decimal
    is_feasible = Column(Boolean, nullable=False, default=True)
    status = Column(String(50), nullable=False, default="draft")
    country_segments_json = Column(JSON, nullable=True)
    certifications_validated = Column(Boolean, nullable=False, default=False)
    operating_countries_validated = Column(Boolean, nullable=False, default=False)
    validation_timestamp = Column(DateTime(timezone=True), nullable=True)
    validation_details = Column(JSON, nullable=True)

    # Relationships
    business_entity = relationship("BusinessEntityModel")
    cargo = relationship("CargoModel")
    origin = relationship("LocationModel", foreign_keys=[origin_id])
    destination = relationship("LocationModel", foreign_keys=[destination_id])
    empty_driving = relationship("EmptyDrivingModel")
    timeline_events = relationship("TimelineEventModel", cascade="all, delete-orphan")
    country_segments = relationship("CountrySegmentModel", cascade="all, delete-orphan")
    status_history = relationship("RouteStatusHistoryModel", back_populates="route", cascade="all, delete-orphan")

    def __init__(self, id, transport_id, business_entity_id,
                 origin_id, destination_id, pickup_time, delivery_time,
                 total_distance_km, total_duration_hours,
                 cargo_id=None, empty_driving_id=None,
                 is_feasible=True, status="draft",
                 timeline_events=None, country_segments_json=None,
                 certifications_validated=False,
                 operating_countries_validated=False,
                 validation_timestamp=None,
                 validation_details=None,
                 country_segments=None):
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
        self.total_distance_km = str(total_distance_km)
        self.total_duration_hours = str(total_duration_hours)  # Convert to string
        self.is_feasible = is_feasible
        self.status = status
        self.timeline_events = timeline_events or []
        self.country_segments_json = country_segments_json or []
        self.certifications_validated = certifications_validated
        self.operating_countries_validated = operating_countries_validated
        self.validation_timestamp = validation_timestamp
        self.validation_details = validation_details or {}
        if country_segments:
            self.country_segments = country_segments

    def to_dict(self):
        """Convert route to dictionary."""
        return {
            'id': str(self.id),
            'transport_id': str(self.transport_id),
            'business_entity_id': str(self.business_entity_id),
            'cargo_id': str(self.cargo_id) if self.cargo_id else None,
            'origin_id': str(self.origin_id),
            'destination_id': str(self.destination_id),
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'empty_driving_id': str(self.empty_driving_id) if self.empty_driving_id else None,
            'total_distance_km': float(self.total_distance_km),
            'total_duration_hours': float(self.total_duration_hours),
            'is_feasible': self.is_feasible,
            'status': self.status,
            'country_segments_json': self.country_segments_json,
            'certifications_validated': self.certifications_validated,
            'operating_countries_validated': self.operating_countries_validated,
            'validation_timestamp': self.validation_timestamp.isoformat() if self.validation_timestamp else None,
            'validation_details': self.validation_details,
            'timeline_events': [event.to_dict() for event in self.timeline_events] if self.timeline_events else [],
            'country_segments': [segment.to_dict() for segment in self.country_segments] if self.country_segments else []
        }


class RouteStatusHistoryModel(Base):
    """Model for route status history."""
    
    __tablename__ = 'route_status_history'
    
    id = Column(String(36), primary_key=True)
    route_id = Column(String(36), ForeignKey('routes.id'), nullable=False)
    status = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    comment = Column(String(500), nullable=True)
    
    # Relationships
    route = relationship("RouteModel", back_populates="status_history")
    
    def __init__(self, id: str, route_id: str, status: str, timestamp: datetime, comment: str = None):
        self.id = id
        self.route_id = route_id
        self.status = status
        self.timestamp = timestamp
        self.comment = comment
        
    def to_dict(self) -> dict:
        """Convert status history to dictionary."""
        return {
            'id': self.id,
            'route_id': self.route_id,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'comment': self.comment
        } 