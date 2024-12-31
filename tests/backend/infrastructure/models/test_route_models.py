"""Tests for route-related SQLAlchemy models."""
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.infrastructure.models.route_models import (
    LocationModel,
    EmptyDrivingModel,
    TimelineEventModel,
    CountrySegmentModel,
    RouteModel
)
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel as TransportTruckSpecModel,
    DriverSpecificationModel as TransportDriverSpecModel
)


@pytest.fixture
def location_data():
    """Fixture for location test data."""
    return {
        "id": str(uuid4()),
        "latitude": 52.520008,
        "longitude": 13.404954,
        "address": "Berlin, Germany"
    }


@pytest.fixture
def empty_driving_data():
    """Fixture for empty driving test data."""
    return {
        "id": str(uuid4()),
        "distance_km": 200.0,
        "duration_hours": 4.0
    }


@pytest.fixture
def timeline_event_data(location_data):
    """Fixture for timeline event test data."""
    return {
        "id": str(uuid4()),
        "route_id": str(uuid4()),  # Will be replaced in tests
        "type": "pickup",
        "location_id": location_data["id"],
        "planned_time": datetime.now(timezone.utc),
        "duration_hours": 1.0,
        "event_order": 1
    }


@pytest.fixture
def country_segment_data(location_data):
    """Fixture for country segment test data."""
    return {
        "id": str(uuid4()),
        "route_id": str(uuid4()),  # Will be replaced in tests
        "country_code": "DE",
        "distance_km": 350.5,
        "duration_hours": 4.5,
        "start_location_id": location_data["id"],
        "end_location_id": str(uuid4())  # Will be replaced with another location
    }


@pytest.fixture
def route_data(location_data, empty_driving_data):
    """Fixture for route test data."""
    pickup_time = datetime.now(timezone.utc)
    delivery_time = pickup_time.replace(hour=(pickup_time.hour + 8) % 24)  # Ensure hours stay within 0-23
    
    return {
        "id": str(uuid4()),
        "transport_id": str(uuid4()),
        "business_entity_id": str(uuid4()),
        "cargo_id": str(uuid4()),
        "origin_id": location_data["id"],
        "destination_id": str(uuid4()),  # Will be replaced with another location
        "pickup_time": pickup_time,
        "delivery_time": delivery_time,
        "empty_driving_id": empty_driving_data["id"],
        "total_distance_km": 550.5,
        "total_duration_hours": 8.5,
        "is_feasible": True
    }


@pytest.fixture
def transport_setup(db, route_data):
    """Fixture to set up transport-related entities."""
    # Create truck specifications
    truck_spec = TransportTruckSpecModel(
        id=str(uuid4()),
        fuel_consumption_empty=22.5,
        fuel_consumption_loaded=29.0,
        toll_class="4_axle",
        euro_class="EURO_6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    db.add(truck_spec)

    # Create driver specifications
    driver_spec = TransportDriverSpecModel(
        id=str(uuid4()),
        daily_rate="138.50",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR", "HACCP"])
    )
    db.add(driver_spec)
    db.commit()

    # Create transport type
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db.add(transport_type)
    db.commit()

    return {
        "truck_spec": truck_spec,
        "driver_spec": driver_spec,
        "transport_type": transport_type
    }


def test_location_model_creation(db, location_data):
    """Test creating a location model."""
    location = LocationModel(**location_data)
    db.add(location)
    db.commit()

    saved_location = db.query(LocationModel).filter_by(id=location_data["id"]).first()
    assert saved_location is not None
    assert saved_location.latitude == str(location_data["latitude"])  # Compare with string
    assert saved_location.longitude == str(location_data["longitude"])  # Compare with string
    assert saved_location.address == location_data["address"]


def test_empty_driving_model_creation(db, empty_driving_data):
    """Test creating an empty driving model."""
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db.add(empty_driving)
    db.commit()

    saved_empty_driving = db.query(EmptyDrivingModel).filter_by(id=empty_driving_data["id"]).first()
    assert saved_empty_driving is not None
    assert saved_empty_driving.distance_km == str(empty_driving_data["distance_km"])  # Compare with string
    assert saved_empty_driving.duration_hours == str(empty_driving_data["duration_hours"])  # Compare with string


def test_timeline_event_model_creation(db, timeline_event_data, location_data, route_data, transport_setup):
    """Test creating a timeline event model."""
    # Create location first
    location = LocationModel(**location_data)
    db.add(location)

    # Create route
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    # Create timeline event
    event = TimelineEventModel(**timeline_event_data)
    db.add(event)
    db.commit()

    saved_event = db.query(TimelineEventModel).filter_by(id=timeline_event_data["id"]).first()
    assert saved_event is not None
    assert saved_event.route_id == timeline_event_data["route_id"]
    assert saved_event.location_id == timeline_event_data["location_id"]
    assert saved_event.type == timeline_event_data["type"]
    # Compare timezone-aware datetimes
    assert saved_event.planned_time.replace(tzinfo=timezone.utc) == timeline_event_data["planned_time"]
    assert saved_event.duration_hours == str(timeline_event_data["duration_hours"])  # Compare with string


def test_country_segment_model_creation(db, country_segment_data, location_data, route_data, transport_setup):
    """Test creating a country segment model."""
    # Create locations first
    location = LocationModel(**location_data)
    db.add(location)

    # Create route
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    # Create country segment
    segment = CountrySegmentModel(**country_segment_data)
    db.add(segment)
    db.commit()

    saved_segment = db.query(CountrySegmentModel).filter_by(id=country_segment_data["id"]).first()
    assert saved_segment is not None
    assert saved_segment.route_id == country_segment_data["route_id"]
    assert saved_segment.country_code == country_segment_data["country_code"]
    assert saved_segment.distance_km == str(country_segment_data["distance_km"])  # Compare with string
    assert saved_segment.duration_hours == str(country_segment_data["duration_hours"])  # Compare with string


def test_route_model_creation(db, route_data, location_data, empty_driving_data, transport_setup):
    """Test creating a route model."""
    # Create locations first
    location = LocationModel(**location_data)
    db.add(location)

    # Create empty driving
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db.add(empty_driving)
    db.commit()

    # Create route
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    saved_route = db.query(RouteModel).filter_by(id=route_data["id"]).first()
    assert saved_route is not None
    assert saved_route.total_distance_km == str(route_data["total_distance_km"])  # Compare with string
    assert saved_route.total_duration_hours == str(route_data["total_duration_hours"])  # Compare with string
    # Compare timezone-aware datetimes
    assert saved_route.pickup_time.replace(tzinfo=timezone.utc) == route_data["pickup_time"]
    assert saved_route.delivery_time.replace(tzinfo=timezone.utc) == route_data["delivery_time"]


def test_route_model_required_fields(db):
    """Test that required fields raise TypeError when missing."""
    # Test that creating a route without required fields raises TypeError
    with pytest.raises(TypeError):
        route = RouteModel(id=str(uuid4()))  # Missing required fields
        db.add(route)
        db.commit()

    # Test that creating a route with all required fields works
    route_id = str(uuid4())
    pickup_time = datetime.now(timezone.utc)
    delivery_time = pickup_time.replace(hour=(pickup_time.hour + 8) % 24)
    
    route = RouteModel(
        id=route_id,
        transport_id=str(uuid4()),
        business_entity_id=str(uuid4()),
        cargo_id=str(uuid4()),
        origin_id=str(uuid4()),
        destination_id=str(uuid4()),
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        empty_driving_id=str(uuid4()),
        total_distance_km=100.0,
        total_duration_hours=2.0
    )
    db.add(route)
    db.commit()

    saved_route = db.query(RouteModel).filter_by(id=route_id).first()
    assert saved_route is not None


def test_route_relationships_cascade_delete(db, route_data, location_data, empty_driving_data, transport_setup):
    """Test that deleting a route cascades to related models."""
    # Create locations first
    location = LocationModel(**location_data)
    db.add(location)

    # Create empty driving
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db.add(empty_driving)
    db.commit()

    # Create route
    route = RouteModel(**route_data)
    db.add(route)
    db.commit()

    # Delete route
    db.delete(route)
    db.commit()

    # Verify cascade delete
    assert db.query(TimelineEventModel).filter_by(route_id=route.id).first() is None
    assert db.query(CountrySegmentModel).filter_by(route_id=route.id).first() is None 