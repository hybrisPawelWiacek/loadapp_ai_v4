"""Tests for cost API endpoints."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from unittest.mock import patch, Mock
from flask import g
from sqlalchemy import text

from backend.domain.entities.cargo import CostSettings, CostBreakdown
from backend.infrastructure.models.route_models import (
    RouteModel, LocationModel, TimelineEventModel, CountrySegmentModel, EmptyDrivingModel
)
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.cargo_models import CargoModel
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.database import SessionLocal


@pytest.fixture
def mock_toll_service():
    """Create a mock toll rate service."""
    with patch("backend.infrastructure.external_services.toll_rate_service.TollRateService") as mock:
        mock_instance = Mock()
        mock_instance.get_toll_rate.return_value = Decimal("0.187")  # Example rate per km
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_cost_settings_data():
    """Create sample cost settings data."""
    return {
        "enabled_components": ["fuel", "toll", "driver", "overhead", "events"],
        "rates": {
            "fuel_rate": "1.5",
            "event_rate": "50.0"
        }
    }


@pytest.fixture
def sample_business(db):
    """Create a sample business entity for testing."""
    business = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Transport Company",
        address="123 Test Street, Test City",
        contact_info={"email": "test@example.com", "phone": "+1234567890"},
        business_type="Transport",
        certifications=["ISO9001", "HACCP"],
        operating_countries=["DE", "PL"],
        cost_overheads={
            "admin": "100.00",
            "insurance": "50.00"
        }
    )
    db.add(business)
    db.commit()
    return business


@pytest.fixture
def sample_transport_type(db):
    """Create a sample transport type for testing."""
    # Create truck specifications
    truck_specs = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="Euro6",
        euro_class="Euro6",
        co2_class="A",
        maintenance_rate_per_km="0.10"
    )
    db.add(truck_specs)
    
    # Create driver specifications
    driver_specs = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.00",
        required_license_type="CE",
        required_certifications=["ADR"]
    )
    db.add(driver_specs)
    
    # Create transport type
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications_id=truck_specs.id,
        driver_specifications_id=driver_specs.id
    )
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
def sample_locations(db):
    """Create sample locations for testing."""
    locations = [
        LocationModel(
            id=str(uuid.uuid4()),
            latitude=52.520008,
            longitude=13.404954,
            address="Berlin, Germany"
        ),
        LocationModel(
            id=str(uuid.uuid4()),
            latitude=52.237049,
            longitude=21.017532,
            address="Warsaw, Poland"
        )
    ]
    for location in locations:
        db.add(location)
    db.commit()
    return locations


@pytest.fixture
def sample_cargo(db, sample_business):
    """Create a sample cargo for testing."""
    cargo = CargoModel(
        id=str(uuid.uuid4()),
        business_entity_id=sample_business.id,
        weight=1000.0,
        volume=10.0,
        cargo_type="general",
        value="5000.00",
        special_requirements=["temperature_controlled", "fragile"],
        status="pending"
    )
    db.add(cargo)
    db.commit()
    return cargo


@pytest.fixture
def sample_empty_driving(db):
    """Create a sample empty driving record."""
    empty_driving = EmptyDrivingModel(
        id=str(uuid.uuid4()),
        distance_km=200.0,  # Fixed empty driving distance
        duration_hours=4.0  # Fixed empty driving duration
    )
    db.add(empty_driving)
    db.commit()
    db.refresh(empty_driving)  # Ensure the record is refreshed
    return empty_driving


@pytest.fixture
def sample_route(db, sample_transport, sample_business, sample_locations, sample_cargo, sample_empty_driving):
    """Create a sample route for testing."""
    # Create main route
    route = RouteModel(
        id=str(uuid.uuid4()),
        transport_id=sample_transport.id,
        business_entity_id=sample_business.id,
        cargo_id=sample_cargo.id,
        origin_id=sample_locations[0].id,
        destination_id=sample_locations[1].id,
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc).replace(hour=23),
        empty_driving_id=sample_empty_driving.id,
        total_distance_km=500.0,
        total_duration_hours=8.0,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.commit()
    
    # Add timeline events
    events = [
        TimelineEventModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            type="pickup",
            location_id=sample_locations[0].id,
            planned_time=route.pickup_time,
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEventModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            type="rest",
            location_id=sample_locations[0].id,
            planned_time=route.pickup_time.replace(hour=12),
            duration_hours=1.0,
            event_order=2
        ),
        TimelineEventModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            type="delivery",
            location_id=sample_locations[1].id,
            planned_time=route.delivery_time,
            duration_hours=1.0,
            event_order=3
        )
    ]

    # Add country segments
    segments = [
        CountrySegmentModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            country_code="DE",
            distance_km=200.0,  # Empty driving
            duration_hours=4.0,
            start_location_id=sample_locations[0].id,
            end_location_id=sample_locations[0].id,
            segment_order=0
        ),
        CountrySegmentModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            country_code="DE",
            distance_km=550.0,
            duration_hours=5.5,
            start_location_id=sample_locations[0].id,
            end_location_id=sample_locations[1].id,
            segment_order=1
        ),
        CountrySegmentModel(
            id=str(uuid.uuid4()),
            route_id=route.id,
            country_code="FR",
            distance_km=500.0,
            duration_hours=4.5,
            start_location_id=sample_locations[1].id,
            end_location_id=sample_locations[1].id,
            segment_order=2
        )
    ]

    db.add_all(events)
    db.add_all(segments)
    db.commit()
    
    # Refresh the route and its relationships
    db.refresh(route)
    for event in events:
        db.refresh(event)
    for segment in segments:
        db.refresh(segment)
    
    return route


def test_create_cost_settings_success(client, db, sample_route, sample_cost_settings_data):
    """Test creating cost settings successfully."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # Create cost settings
    response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert response.status_code == 200
    
    # Verify response
    settings = response.get_json()["settings"]
    assert settings["route_id"] == str(route.id)
    assert settings["enabled_components"] == sample_cost_settings_data["enabled_components"]
    assert all(str(v) == settings["rates"][k] for k, v in sample_cost_settings_data["rates"].items())


def test_create_cost_settings_invalid_route(client, sample_cost_settings_data):
    """Test cost settings creation with invalid route."""
    invalid_id = str(uuid.uuid4())
    response = client.post(
        f"/api/cost/settings/{invalid_id}",
        json=sample_cost_settings_data
    )
    
    assert response.status_code == 404
    assert response.get_json()["error"] == "Route not found"


def test_calculate_costs_success(client, db, sample_route, sample_cost_settings_data):
    """Test calculating costs successfully."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # First create cost settings
    settings_response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert settings_response.status_code == 200
    
    # Then calculate costs
    response = client.post(f"/api/cost/calculate/{route.id}")
    assert response.status_code == 200
    
    # Verify response
    breakdown = response.get_json()["breakdown"]
    assert breakdown["route_id"] == str(route.id)
    assert all(isinstance(v, str) for v in breakdown["fuel_costs"].values())
    assert all(isinstance(v, str) for v in breakdown["toll_costs"].values())
    assert isinstance(breakdown["driver_costs"], str)
    assert isinstance(breakdown["overhead_costs"], str)
    assert isinstance(breakdown["total_cost"], str)


def test_calculate_costs_invalid_route(client):
    """Test cost calculation with invalid route."""
    invalid_id = str(uuid.uuid4())
    response = client.post(f"/api/cost/calculate/{invalid_id}")
    
    assert response.status_code == 404
    assert response.get_json()["error"] == "Route not found"


def test_get_cost_breakdown_success(client, db, sample_route, sample_cost_settings_data):
    """Test getting cost breakdown successfully."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # First create cost settings
    settings_response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert settings_response.status_code == 200
    
    # Then calculate costs
    calc_response = client.post(f"/api/cost/calculate/{route.id}")
    assert calc_response.status_code == 200
    
    # Finally get the breakdown
    response = client.get(f"/api/cost/breakdown/{route.id}")
    assert response.status_code == 200
    
    # Verify response
    breakdown = response.get_json()["breakdown"]
    assert breakdown["route_id"] == str(route.id)
    assert all(isinstance(v, str) for v in breakdown["fuel_costs"].values())
    assert all(isinstance(v, str) for v in breakdown["toll_costs"].values())
    assert isinstance(breakdown["driver_costs"], str)
    assert isinstance(breakdown["overhead_costs"], str)
    assert isinstance(breakdown["total_cost"], str)


def test_get_cost_breakdown_not_found(client, db, sample_route):
    """Test cost breakdown retrieval when not found."""
    # Verify route exists
    route = db.query(RouteModel).filter_by(id=sample_route.id).first()
    assert route is not None, "Route not found in database"
    
    response = client.get(f"/api/cost/breakdown/{sample_route.id}")
    
    assert response.status_code == 404
    assert response.get_json()["error"] == "Cost breakdown not found. Please calculate costs first."


def test_get_cost_settings_success(client, db, sample_route, sample_cost_settings_data):
    """Test getting cost settings successfully."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # First create cost settings
    settings_response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert settings_response.status_code == 200
    
    # Then get the settings
    response = client.get(f"/api/cost/settings/{route.id}")
    assert response.status_code == 200
    
    # Verify response
    settings = response.get_json()["settings"]
    assert settings["route_id"] == str(route.id)
    assert settings["enabled_components"] == sample_cost_settings_data["enabled_components"]
    assert all(str(v) == settings["rates"][k] for k, v in sample_cost_settings_data["rates"].items())


def test_update_cost_settings_success(client, db, sample_route, sample_cost_settings_data):
    """Test updating cost settings successfully."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # First create cost settings
    settings_response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert settings_response.status_code == 200
    
    # Update settings
    updated_settings = {
        "enabled_components": ["fuel", "toll"],
        "rates": {
            "fuel_rate": "2.0",
            "event_rate": "75.0"
        }
    }
    
    response = client.put(f"/api/cost/settings/{route.id}", json=updated_settings)
    assert response.status_code == 200
    
    # Verify response
    settings = response.get_json()["settings"]
    assert settings["route_id"] == str(route.id)
    assert settings["enabled_components"] == updated_settings["enabled_components"]
    assert all(str(v) == settings["rates"][k] for k, v in updated_settings["rates"].items())


def test_calculate_route_cost(client, db, sample_route, sample_cost_settings_data):
    """Test calculating route cost."""
    # Get a fresh instance of the route from the database
    route = db.get(RouteModel, sample_route.id)
    db.refresh(route)
    
    # First create cost settings
    settings_response = client.post(f"/api/cost/settings/{route.id}", json=sample_cost_settings_data)
    assert settings_response.status_code == 200
    
    # Calculate costs
    response = client.post(f"/api/cost/calculate/{route.id}")
    assert response.status_code == 200
    
    # Verify response
    breakdown = response.get_json()["breakdown"]
    assert breakdown["route_id"] == str(route.id)
    assert all(isinstance(v, str) for v in breakdown["fuel_costs"].values())
    assert all(isinstance(v, str) for v in breakdown["toll_costs"].values())
    assert isinstance(breakdown["driver_costs"], str)
    assert isinstance(breakdown["overhead_costs"], str)
    assert isinstance(breakdown["total_cost"], str) 