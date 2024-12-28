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
def transport_setup(db_session, route_data):
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
    db_session.add(truck_spec)

    # Create driver specifications
    driver_spec = TransportDriverSpecModel(
        id=str(uuid4()),
        daily_rate="138.50",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR", "HACCP"])
    )
    db_session.add(driver_spec)
    db_session.commit()

    # Create transport type
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db_session.add(transport_type)
    db_session.commit()

    return {
        "truck_spec": truck_spec,
        "driver_spec": driver_spec,
        "transport_type": transport_type
    }


def test_location_model_creation(db_session, location_data):
    """Test creating a location model."""
    location = LocationModel(**location_data)
    db_session.add(location)
    db_session.commit()

    saved_location = db_session.query(LocationModel).filter_by(id=location_data["id"]).first()
    assert saved_location is not None
    assert saved_location.latitude == location_data["latitude"]
    assert saved_location.longitude == location_data["longitude"]
    assert saved_location.address == location_data["address"]


def test_empty_driving_model_creation(db_session, empty_driving_data):
    """Test creating an empty driving model."""
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db_session.add(empty_driving)
    db_session.commit()

    saved_driving = db_session.query(EmptyDrivingModel).filter_by(id=empty_driving_data["id"]).first()
    assert saved_driving is not None
    assert saved_driving.distance_km == empty_driving_data["distance_km"]
    assert saved_driving.duration_hours == empty_driving_data["duration_hours"]


def test_timeline_event_model_creation(db_session, timeline_event_data, location_data, route_data, transport_setup):
    """Test creating a timeline event model with location relationship."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    # Create required related entities first
    from backend.infrastructure.models.business_models import BusinessEntityModel
    from backend.infrastructure.models.cargo_models import CargoModel

    # Create business entity
    business_entity = BusinessEntityModel(
        id=route_data["business_entity_id"],
        name="Test Business",
        certifications=json.dumps([]),
        operating_countries=json.dumps([]),
        cost_overheads=json.dumps({})
    )
    db_session.add(business_entity)

    # Create transport
    transport = TransportModel(
        id=route_data["transport_id"],
        transport_type_id="flatbed",
        business_entity_id=route_data["business_entity_id"],
        truck_specifications_id=transport_setup["truck_spec"].id,
        driver_specifications_id=transport_setup["driver_spec"].id,
        is_active=True
    )
    db_session.add(transport)

    # Create cargo
    cargo = CargoModel(
        id=route_data["cargo_id"],
        weight=1000.0,
        value="5000.00",
        special_requirements=json.dumps([])
    )
    db_session.add(cargo)

    # Create locations
    origin = LocationModel(**location_data)
    db_session.add(origin)

    destination_data = {**location_data, "id": route_data["destination_id"]}
    destination = LocationModel(**destination_data)
    db_session.add(destination)

    # Create empty driving
    empty_driving = EmptyDrivingModel(
        id=route_data["empty_driving_id"],
        distance_km=200.0,
        duration_hours=4.0
    )
    db_session.add(empty_driving)
    db_session.commit()

    # Create route
    route = RouteModel(**route_data)
    db_session.add(route)
    db_session.commit()

    # Update timeline event with route ID
    timeline_event_data["route_id"] = route.id

    # Create timeline event
    event = TimelineEventModel(**timeline_event_data)
    db_session.add(event)
    db_session.commit()

    saved_event = db_session.query(TimelineEventModel).filter_by(id=timeline_event_data["id"]).first()
    assert saved_event is not None
    assert saved_event.type == timeline_event_data["type"]
    assert saved_event.duration_hours == timeline_event_data["duration_hours"]
    assert saved_event.event_order == timeline_event_data["event_order"]
    assert saved_event.location.id == location_data["id"]


def test_country_segment_model_creation(db_session, country_segment_data, location_data, route_data, transport_setup):
    """Test creating a country segment model with location relationships."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    # Create required related entities first
    from backend.infrastructure.models.business_models import BusinessEntityModel
    from backend.infrastructure.models.cargo_models import CargoModel

    # Create business entity
    business_entity = BusinessEntityModel(
        id=route_data["business_entity_id"],
        name="Test Business",
        certifications=json.dumps([]),
        operating_countries=json.dumps([]),
        cost_overheads=json.dumps({})
    )
    db_session.add(business_entity)

    # Create transport
    transport = TransportModel(
        id=route_data["transport_id"],
        transport_type_id="flatbed",
        business_entity_id=route_data["business_entity_id"],
        truck_specifications_id=transport_setup["truck_spec"].id,
        driver_specifications_id=transport_setup["driver_spec"].id,
        is_active=True
    )
    db_session.add(transport)

    # Create cargo
    cargo = CargoModel(
        id=route_data["cargo_id"],
        weight=1000.0,
        value="5000.00",
        special_requirements=json.dumps([])
    )
    db_session.add(cargo)

    # Create locations for route
    origin = LocationModel(**location_data)
    db_session.add(origin)

    destination_data = {**location_data, "id": route_data["destination_id"], "address": "Munich, Germany"}
    destination = LocationModel(**destination_data)
    db_session.add(destination)

    # Create empty driving
    empty_driving = EmptyDrivingModel(
        id=route_data["empty_driving_id"],
        distance_km=200.0,
        duration_hours=4.0
    )
    db_session.add(empty_driving)
    db_session.commit()

    # Create route
    route = RouteModel(**route_data)
    db_session.add(route)
    db_session.commit()

    # Update country segment with route ID and use existing locations
    country_segment_data["route_id"] = route.id
    country_segment_data["start_location_id"] = location_data["id"]  # Use existing origin location
    country_segment_data["end_location_id"] = route_data["destination_id"]  # Use existing destination location

    # Create country segment
    segment = CountrySegmentModel(**country_segment_data)
    db_session.add(segment)
    db_session.commit()

    saved_segment = db_session.query(CountrySegmentModel).filter_by(id=country_segment_data["id"]).first()
    assert saved_segment is not None
    assert saved_segment.country_code == country_segment_data["country_code"]
    assert saved_segment.distance_km == country_segment_data["distance_km"]
    assert saved_segment.duration_hours == country_segment_data["duration_hours"]
    assert saved_segment.start_location.id == country_segment_data["start_location_id"]
    assert saved_segment.end_location.id == country_segment_data["end_location_id"]


def test_route_model_creation(db_session, route_data, location_data, empty_driving_data, transport_setup):
    """Test creating a route model with all relationships."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    # Create required related entities first
    from backend.infrastructure.models.business_models import BusinessEntityModel
    from backend.infrastructure.models.cargo_models import CargoModel

    # Create business entity
    business_entity = BusinessEntityModel(
        id=route_data["business_entity_id"],
        name="Test Business",
        certifications=json.dumps([]),
        operating_countries=json.dumps([]),
        cost_overheads=json.dumps({})
    )
    db_session.add(business_entity)

    # Create transport
    transport = TransportModel(
        id=route_data["transport_id"],
        transport_type_id="flatbed",
        business_entity_id=route_data["business_entity_id"],
        truck_specifications_id=transport_setup["truck_spec"].id,
        driver_specifications_id=transport_setup["driver_spec"].id,
        is_active=True
    )
    db_session.add(transport)

    # Create cargo
    cargo = CargoModel(
        id=route_data["cargo_id"],
        weight=1000.0,
        value="5000.00",
        special_requirements=json.dumps([])
    )
    db_session.add(cargo)

    # Create origin location
    origin = LocationModel(**location_data)
    db_session.add(origin)

    # Create destination location
    destination_data = {**location_data, "id": route_data["destination_id"]}
    destination = LocationModel(**destination_data)
    db_session.add(destination)

    # Create empty driving
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db_session.add(empty_driving)

    db_session.commit()

    # Create route
    route = RouteModel(**route_data)
    db_session.add(route)
    db_session.commit()

    saved_route = db_session.query(RouteModel).filter_by(id=route_data["id"]).first()
    assert saved_route is not None
    assert saved_route.transport_id == route_data["transport_id"]
    assert saved_route.business_entity_id == route_data["business_entity_id"]
    assert saved_route.cargo_id == route_data["cargo_id"]
    assert saved_route.origin.id == location_data["id"]
    assert saved_route.destination.id == route_data["destination_id"]
    assert saved_route.empty_driving.id == empty_driving_data["id"]
    assert saved_route.total_distance_km == route_data["total_distance_km"]
    assert saved_route.total_duration_hours == route_data["total_duration_hours"]
    assert saved_route.is_feasible == route_data["is_feasible"]


def test_route_model_required_fields(db_session):
    """Test that required fields raise IntegrityError when missing."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    with pytest.raises(IntegrityError):
        route = RouteModel(id=str(uuid4()))  # Missing required fields
        db_session.add(route)
        db_session.commit()


def test_route_relationships_cascade_delete(db_session, route_data, location_data, empty_driving_data, transport_setup):
    """Test that deleting a route doesn't delete related entities but deletes dependent ones."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))

    # Create business entity
    from backend.infrastructure.models.business_models import BusinessEntityModel
    from backend.infrastructure.models.cargo_models import CargoModel

    business_entity = BusinessEntityModel(
        id=route_data["business_entity_id"],
        name="Test Business",
        certifications=json.dumps([]),
        operating_countries=json.dumps([]),
        cost_overheads=json.dumps({})
    )
    db_session.add(business_entity)

    # Create transport
    transport = TransportModel(
        id=route_data["transport_id"],
        transport_type_id="flatbed",
        business_entity_id=route_data["business_entity_id"],
        truck_specifications_id=transport_setup["truck_spec"].id,
        driver_specifications_id=transport_setup["driver_spec"].id,
        is_active=True
    )
    db_session.add(transport)

    # Create cargo
    cargo = CargoModel(
        id=route_data["cargo_id"],
        weight=1000.0,
        value="5000.00",
        special_requirements=json.dumps([])
    )
    db_session.add(cargo)

    # Create origin location
    origin = LocationModel(**location_data)
    db_session.add(origin)

    # Create destination location
    destination_data = {**location_data, "id": route_data["destination_id"]}
    destination = LocationModel(**destination_data)
    db_session.add(destination)

    # Create empty driving
    empty_driving = EmptyDrivingModel(**empty_driving_data)
    db_session.add(empty_driving)

    # Create route
    route = RouteModel(**route_data)
    db_session.add(route)
    db_session.commit()

    # Add timeline events and country segments
    event_data = {
        "id": str(uuid4()),
        "route_id": route_data["id"],
        "type": "pickup",
        "location_id": location_data["id"],
        "planned_time": datetime.now(timezone.utc),
        "duration_hours": 1.0,
        "event_order": 1
    }
    event = TimelineEventModel(**event_data)
    db_session.add(event)

    segment_data = {
        "id": str(uuid4()),
        "route_id": route_data["id"],
        "country_code": "DE",
        "distance_km": 350.5,
        "duration_hours": 4.5,
        "start_location_id": location_data["id"],
        "end_location_id": route_data["destination_id"]
    }
    segment = CountrySegmentModel(**segment_data)
    db_session.add(segment)
    db_session.commit()

    # Delete route
    route = db_session.query(RouteModel).filter_by(id=route_data["id"]).first()
    db_session.delete(route)
    db_session.commit()

    # Verify timeline events and country segments are deleted
    assert db_session.query(TimelineEventModel).filter_by(id=event_data["id"]).first() is None
    assert db_session.query(CountrySegmentModel).filter_by(id=segment_data["id"]).first() is None

    # Verify other related entities still exist
    assert db_session.query(LocationModel).filter_by(id=location_data["id"]).first() is not None
    assert db_session.query(EmptyDrivingModel).filter_by(id=empty_driving_data["id"]).first() is not None 