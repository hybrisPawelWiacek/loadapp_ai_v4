"""Tests for route API endpoints."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from unittest.mock import patch, Mock
from flask import Flask

from backend.app import create_app
from backend.domain.entities.location import Location
from backend.domain.entities.route import Route, EmptyDriving, TimelineEvent, CountrySegment
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.cargo_models import CargoModel
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.route_models import LocationModel
from backend.infrastructure.database import SessionLocal


@pytest.fixture
def mock_googlemaps():
    """Create a mock Google Maps client."""
    with patch("backend.infrastructure.external_services.google_maps_service.googlemaps.Client") as mock:
        mock_instance = Mock()
        
        # Mock directions response
        mock_instance.directions.return_value = [{
            'legs': [{
                'distance': {'value': 500000},  # 500 km
                'duration': {'value': 18000},    # 5 hours
                'steps': [{
                    'html_instructions': 'Drive from Berlin to Warsaw',
                    'distance': {'value': 500000},
                    'duration': {'value': 18000},
                    'start_location': {'lat': 52.520008, 'lng': 13.404954},
                    'end_location': {'lat': 52.237049, 'lng': 21.017532}
                }]
            }]
        }]
        
        # Mock distance matrix response
        mock_instance.distance_matrix.return_value = {
            'rows': [{
                'elements': [{
                    'distance': {'value': 500000},
                    'duration': {'value': 18000},
                    'status': 'OK'
                }]
            }]
        }
        
        # Mock geocode response for Berlin
        mock_instance.geocode.side_effect = [
            [{  # Berlin
                'geometry': {
                    'location': {'lat': 52.520008, 'lng': 13.404954}
                },
                'address_components': [
                    {'types': ['country'], 'short_name': 'DE'}
                ]
            }],
            [{  # Warsaw
                'geometry': {
                    'location': {'lat': 52.237049, 'lng': 21.017532}
                },
                'address_components': [
                    {'types': ['country'], 'short_name': 'PL'}
                ]
            }]
        ]
        
        # Mock reverse geocode response
        mock_instance.reverse_geocode.side_effect = [
            [{  # Berlin
                'address_components': [
                    {'types': ['country'], 'short_name': 'DE'}
                ]
            }],
            [{  # Warsaw
                'address_components': [
                    {'types': ['country'], 'short_name': 'PL'}
                ]
            }]
        ]
        
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def app(test_config, mock_googlemaps):
    """Create Flask test app."""
    app = create_app(test_config)
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def db():
    """Create test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def sample_locations(db):
    """Create sample locations for testing."""
    origin = LocationModel(
        id=str(uuid.uuid4()),
        latitude="52.520008",
        longitude="13.404954",
        address="Berlin, Germany"
    )
    destination = LocationModel(
        id=str(uuid.uuid4()),
        latitude="52.237049",
        longitude="21.017532",
        address="Warsaw, Poland"
    )
    db.add(origin)
    db.add(destination)
    db.commit()
    return origin, destination


@pytest.fixture
def sample_business(db):
    """Create a sample business entity for testing."""
    business = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info={
            "email": "test@example.com",
            "phone": "+49123456789"
        },
        business_type="TRANSPORT_COMPANY",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": "100.00"}
    )
    db.add(business)
    db.commit()
    return business


@pytest.fixture
def sample_transport_type(db):
    """Create a sample transport type for testing."""
    # Create specifications
    truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    
    driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.0",
        required_license_type="CE",
        required_certifications='["ADR"]'
    )
    
    # Create transport type with unique ID
    transport_type = TransportTypeModel(
        id=f"flatbed_{str(uuid.uuid4())}",  # Make ID unique
        name="Flatbed",
        truck_specifications=truck_spec,
        driver_specifications=driver_spec
    )
    
    db.add(truck_spec)
    db.add(driver_spec)
    db.add(transport_type)
    db.commit()
    
    return transport_type


@pytest.fixture
def sample_transport(db, sample_business, sample_transport_type):
    """Create a sample transport for testing."""
    transport = TransportModel(
        id=str(uuid.uuid4()),
        transport_type_id=sample_transport_type.id,
        business_entity_id=sample_business.id,
        truck_specifications_id=sample_transport_type.truck_specifications_id,
        driver_specifications_id=sample_transport_type.driver_specifications_id,
        is_active=True
    )
    db.add(transport)
    db.commit()
    return transport


@pytest.fixture
def sample_cargo(db, sample_business):
    """Create a sample cargo for testing."""
    cargo = CargoModel(
        id=str(uuid.uuid4()),
        business_entity_id=sample_business.id,
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value=str(Decimal("25000.00")),
        special_requirements=["temperature_controlled"],
        status="pending"
    )
    db.add(cargo)
    db.commit()
    return cargo


@pytest.fixture
def route_calculation_data(sample_transport, sample_cargo, sample_locations):
    """Create test data for route calculation."""
    origin, destination = sample_locations
    now = datetime.now(timezone.utc)
    return {
        "transport_id": sample_transport.id,
        "cargo_id": sample_cargo.id,
        "origin_id": origin.id,
        "destination_id": destination.id,
        "pickup_time": now.isoformat(),
        "delivery_time": (now + timedelta(days=1)).isoformat()
    }


def test_calculate_route_success(client, route_calculation_data):
    """Test successful route calculation."""
    response = client.post("/api/route/calculate", json=route_calculation_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "route" in data
    route = data["route"]
    
    # Check route details
    assert route["transport_id"] == route_calculation_data["transport_id"]
    assert route["cargo_id"] == route_calculation_data["cargo_id"]
    assert route["origin_id"] == route_calculation_data["origin_id"]
    assert route["destination_id"] == route_calculation_data["destination_id"]
    
    # Check empty driving ID
    assert "empty_driving_id" in route
    assert uuid.UUID(route["empty_driving_id"])
    
    # Check timeline events
    events = route["timeline_events"]
    assert len(events) == 3  # pickup, rest, delivery
    assert events[0]["type"] == "pickup"
    assert events[1]["type"] == "rest"
    assert events[2]["type"] == "delivery"
    assert all(event["duration_hours"] == 1.0 for event in events)
    
    # Check country segments
    assert "country_segments" in route
    assert len(route["country_segments"]) > 0
    for segment in route["country_segments"]:
        assert "country_code" in segment
        assert "distance_km" in segment
        assert "duration_hours" in segment
    
    # Check feasibility (always true in PoC)
    assert route["is_feasible"] is True


def test_calculate_route_invalid_transport(client, route_calculation_data):
    """Test route calculation with invalid transport ID."""
    route_calculation_data["transport_id"] = str(uuid.uuid4())
    response = client.post("/api/route/calculate", json=route_calculation_data)
    assert response.status_code == 404
    assert "Transport not found" in response.get_json()["error"]


def test_calculate_route_invalid_cargo(client, route_calculation_data):
    """Test route calculation with invalid cargo ID."""
    route_calculation_data["cargo_id"] = str(uuid.uuid4())
    response = client.post("/api/route/calculate", json=route_calculation_data)
    assert response.status_code == 404
    assert "Cargo not found" in response.get_json()["error"]


def test_calculate_route_invalid_dates(client, route_calculation_data):
    """Test route calculation with invalid dates."""
    now = datetime.now(timezone.utc)
    route_calculation_data["pickup_time"] = now.isoformat()
    route_calculation_data["delivery_time"] = (now - timedelta(hours=1)).isoformat()
    response = client.post("/api/route/calculate", json=route_calculation_data)
    assert response.status_code == 400
    assert "Delivery time must be after pickup time" in response.get_json()["error"]


def test_check_route_feasibility(client, route_calculation_data):
    """Test route feasibility check."""
    response = client.post("/api/route/check-feasibility", json=route_calculation_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "is_feasible" in data
    assert data["is_feasible"] is True  # Always true in PoC
    assert "validation_details" in data


def test_get_route_timeline(client, route_calculation_data):
    """Test getting route timeline."""
    # First, create a route
    response = client.post("/api/route/calculate", json=route_calculation_data)
    assert response.status_code == 200
    route_data = response.get_json()
    route_id = route_data["route"]["id"]
    
    # Then, get its timeline
    response = client.get(f"/api/route/{route_id}/timeline")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "timeline_events" in data
    assert len(data["timeline_events"]) > 0
    
    # Verify timeline event structure
    event = data["timeline_events"][0]
    assert "id" in event
    assert "type" in event
    assert "location" in event
    assert "planned_time" in event
    assert "duration_hours" in event
    assert "event_order" in event


def test_get_route_segments(client, route_calculation_data):
    """Test getting route segments."""
    # First calculate route
    calc_response = client.post("/api/route/calculate", json=route_calculation_data)
    assert calc_response.status_code == 200
    route_id = calc_response.get_json()["route"]["id"]
    
    # Then get segments
    response = client.get(f"/api/route/{route_id}/segments")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "country_segments" in data
    segments = data["country_segments"]
    assert len(segments) > 0
    
    # Check segment details
    for segment in segments:
        assert "country_code" in segment
        assert "distance_km" in segment
        assert "duration_hours" in segment
        assert "start_location" in segment
        assert "end_location" in segment


def test_update_route_timeline(client, route_calculation_data):
    """Test updating route timeline."""
    # First calculate route
    calc_response = client.post("/api/route/calculate", json=route_calculation_data)
    assert calc_response.status_code == 200
    route_id = calc_response.get_json()["route"]["id"]
    
    # Then update timeline
    now = datetime.now(timezone.utc)
    update_data = {
        "timeline_events": [
            {
                "type": "pickup",
                "planned_time": now.isoformat(),
                "duration_hours": 1.0,
                "event_order": 1
            },
            {
                "type": "rest",
                "planned_time": (now + timedelta(hours=4)).isoformat(),
                "duration_hours": 1.0,
                "event_order": 2
            },
            {
                "type": "delivery",
                "planned_time": (now + timedelta(hours=8)).isoformat(),
                "duration_hours": 1.0,
                "event_order": 3
            }
        ]
    }
    
    response = client.put(f"/api/route/{route_id}/timeline", json=update_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "timeline_events" in data
    events = data["timeline_events"]
    assert len(events) == 3
    
    # Check event details
    for event in events:
        assert "id" in event
        assert "type" in event
        assert "location" in event
        assert "planned_time" in event
        assert "duration_hours" in event
        assert "event_order" in event


def test_update_route_timeline_invalid_sequence(client, route_calculation_data):
    """Test updating route timeline with invalid sequence."""
    # First calculate route
    calc_response = client.post("/api/route/calculate", json=route_calculation_data)
    assert calc_response.status_code == 200
    route_id = calc_response.get_json()["route"]["id"]
    
    # Then update timeline with invalid sequence
    now = datetime.now(timezone.utc)
    update_data = {
        "timeline_events": [
            {
                "type": "rest",  # Should be pickup
                "planned_time": now.isoformat(),
                "duration_hours": 1.0,
                "event_order": 1
            }
        ]
    }
    
    response = client.put(f"/api/route/{route_id}/timeline", json=update_data)
    assert response.status_code == 400
    assert "Invalid timeline sequence" in response.get_json()["error"] 