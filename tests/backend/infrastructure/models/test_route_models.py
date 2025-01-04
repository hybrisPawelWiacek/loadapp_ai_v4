"""Tests for route-related SQLAlchemy models."""
import json
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.infrastructure.models.route_models import (
    RouteModel,
    LocationModel,
    EmptyDrivingModel,
    TimelineEventModel,
    CountrySegmentModel
)


@pytest.fixture
def timeline_event_data(test_data):
    """Fixture for timeline event test data."""
    return {
        "id": str(uuid4()),
        "route_id": test_data["route"].id,
        "type": "pickup",
        "location_id": test_data["origin"].id,
        "planned_time": datetime.now(timezone.utc),
        "duration_hours": 1.0,
        "event_order": 1
    }


@pytest.fixture
def country_segment_data(test_data):
    """Fixture for country segment test data."""
    return {
        "id": str(uuid4()),
        "route_id": test_data["route"].id,
        "country_code": "DE",
        "distance_km": 350.5,
        "duration_hours": 4.5,
        "start_location_id": test_data["origin"].id,
        "end_location_id": test_data["destination"].id,
        "segment_order": 0
    }


@pytest.fixture
def route_data(test_data):
    """Fixture for route test data."""
    return {
        "id": str(uuid4()),
        "transport_id": test_data["transport"].id,
        "business_entity_id": test_data["business_entity"].id,
        "cargo_id": test_data["cargo"].id,
        "origin_id": test_data["origin"].id,
        "destination_id": test_data["destination"].id,
        "pickup_time": datetime.now(timezone.utc),
        "delivery_time": datetime.now(timezone.utc).replace(hour=(datetime.now().hour + 8) % 24),
        "empty_driving_id": test_data["empty_driving"].id,
        "total_distance_km": 100.0,
        "total_duration_hours": 2.0,
        "is_feasible": True,
        "status": "draft"
    }


def test_timeline_event_model_creation(db, timeline_event_data):
    """Test creating a timeline event model."""
    event = TimelineEventModel(**timeline_event_data)
    db.add(event)
    db.commit()

    saved_event = db.query(TimelineEventModel).filter_by(id=timeline_event_data["id"]).first()
    assert saved_event is not None
    assert saved_event.route_id == timeline_event_data["route_id"]
    assert saved_event.type == timeline_event_data["type"]
    assert saved_event.duration_hours == str(timeline_event_data["duration_hours"])


def test_country_segment_model_creation(db, country_segment_data):
    """Test creating a country segment model."""
    segment = CountrySegmentModel(**country_segment_data)
    db.add(segment)
    db.commit()

    saved_segment = db.query(CountrySegmentModel).filter_by(id=country_segment_data["id"]).first()
    assert saved_segment is not None
    assert saved_segment.route_id == country_segment_data["route_id"]
    assert saved_segment.country_code == country_segment_data["country_code"]
    assert saved_segment.distance_km == str(country_segment_data["distance_km"])
    assert saved_segment.duration_hours == str(country_segment_data["duration_hours"])


def test_route_model_creation(db, route_data):
    """Test creating a route model."""
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    saved_route = db.query(RouteModel).filter_by(id=route_data["id"]).first()
    assert saved_route is not None
    assert saved_route.transport_id == route_data["transport_id"]
    assert saved_route.business_entity_id == route_data["business_entity_id"]
    assert saved_route.cargo_id == route_data["cargo_id"]
    assert saved_route.origin_id == route_data["origin_id"]
    assert saved_route.destination_id == route_data["destination_id"]
    assert saved_route.empty_driving_id == route_data["empty_driving_id"]
    assert float(saved_route.total_distance_km) == float(route_data["total_distance_km"])
    assert float(saved_route.total_duration_hours) == float(route_data["total_duration_hours"])
    assert saved_route.is_feasible == route_data["is_feasible"]
    assert saved_route.status == route_data["status"]


def test_route_model_required_fields(db, route_data):
    """Test that required fields raise IntegrityError when missing."""
    # Test missing transport_id
    invalid_route = route_data.copy()
    invalid_route.pop("transport_id")
    with pytest.raises((IntegrityError, TypeError)):
        route = RouteModel(**invalid_route)
        db.add(route)
        db.commit()
    db.rollback()

    # Test missing business_entity_id
    invalid_route = route_data.copy()
    invalid_route.pop("business_entity_id")
    with pytest.raises((IntegrityError, TypeError)):
        route = RouteModel(**invalid_route)
        db.add(route)
        db.commit()
    db.rollback()

    # Test missing cargo_id
    invalid_route = route_data.copy()
    invalid_route.pop("cargo_id")
    with pytest.raises((IntegrityError, TypeError)):
        route = RouteModel(**invalid_route)
        db.add(route)
        db.commit()
    db.rollback()


def test_route_relationships_cascade_delete(db, route_data, timeline_event_data, country_segment_data):
    """Test that deleting a route cascades to related entities."""
    # Create route
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    # Create timeline event with the route ID
    event_data = timeline_event_data.copy()
    event_data["route_id"] = route.id
    event = TimelineEventModel(**event_data)
    db.add(event)

    # Create country segment with the route ID
    segment_data = country_segment_data.copy()
    segment_data["route_id"] = route.id
    segment = CountrySegmentModel(**segment_data)
    db.add(segment)
    db.commit()

    # Delete route
    db.delete(route)
    db.commit()

    # Verify cascade delete
    assert db.query(TimelineEventModel).filter_by(id=event.id).first() is None
    assert db.query(CountrySegmentModel).filter_by(id=segment.id).first() is None 