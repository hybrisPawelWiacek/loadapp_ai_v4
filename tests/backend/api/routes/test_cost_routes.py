"""Tests for cost routes."""
import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from flask import g

from backend.domain.entities.rate_types import get_default_validation_schemas
from backend.infrastructure.models.cargo_models import CostBreakdownModel
from backend.infrastructure.models.rate_models import RateValidationRuleModel
from backend.infrastructure.models.route_models import (
    RouteModel, LocationModel
)
from backend.infrastructure.models.transport_models import (
    TransportTypeModel, TruckSpecificationModel,
    DriverSpecificationModel, TransportModel
)
from backend.infrastructure.models.business_models import BusinessEntityModel

@pytest.fixture
def route_with_settings(client, db):
    """Create a route with cost settings for testing."""
    # Initialize rate validation rules
    default_schemas = get_default_validation_schemas()
    for schema in default_schemas.values():
        model = RateValidationRuleModel.from_domain(schema)
        db.add(model)
    
    # Create business entity
    business = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Transport Co",
        address="Test Address",
        contact_info=json.dumps({"email": "test@example.com"}),
        business_type="TRANSPORT_COMPANY",
        certifications=json.dumps(["ISO9001"]),
        operating_countries=json.dumps(["DE", "PL"]),
        cost_overheads=json.dumps({"admin": "100.00"})
    )
    db.add(business)
    
    # Create truck and driver specifications
    truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    db.add(truck_spec)
    
    driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.0",
        driving_time_rate="25.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    db.add(driver_spec)
    
    # Create transport type and transport
    transport_type = TransportTypeModel(
        id=str(uuid.uuid4()),
        name="Flatbed",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db.add(transport_type)
    
    transport = TransportModel(
        id=str(uuid.uuid4()),
        transport_type_id=transport_type.id,
        business_entity_id=business.id,
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id,
        is_active=True
    )
    db.add(transport)
    
    # Create origin and destination locations
    origin = LocationModel(
        id=str(uuid.uuid4()),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin, Germany"
    )
    db.add(origin)
    
    destination = LocationModel(
        id=str(uuid.uuid4()),
        latitude=52.237049,
        longitude=21.017532,
        address="Warsaw, Poland"
    )
    db.add(destination)
    
    # Create route
    route = RouteModel(
        id=str(uuid.uuid4()),
        transport_id=transport.id,
        business_entity_id=business.id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        total_distance_km=500.0,
        total_duration_hours=8.0,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.flush()
    
    # Create initial cost settings
    response = client.post(
        f"/api/cost/settings/{route.id}",
        json={
            "enabled_components": ["fuel", "toll", "driver"],
            "rates": {
                "fuel_rate": "2.50",
                "toll_rate": "0.25",
                "driver_base_rate": "200.00"
            }
        }
    )
    assert response.status_code == 200
    
    db.commit()
    return route

def test_update_cost_settings_partial_success(client, route_with_settings):
    """Test successful partial update of cost settings."""
    # Prepare test data
    update_data = {
        "rates": {
            "fuel_rate": "2.75",
            "driver_base_rate": "220.00"
        }
    }
    
    # Make request
    response = client.patch(
        f"/api/cost/settings/{route_with_settings.id}",
        json=update_data
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json
    assert data["rates"]["fuel_rate"] == "2.75"
    assert data["rates"]["driver_base_rate"] == "220.00"
    # Other rates should remain unchanged
    assert "toll_rate" in data["rates"]

def test_update_cost_settings_partial_invalid_rates(client, route_with_settings):
    """Test partial update with invalid rate values."""
    update_data = {
        "rates": {
            "fuel_rate": "10.0"  # Above max allowed
        }
    }
    
    response = client.patch(
        f"/api/cost/settings/{route_with_settings.id}",
        json=update_data
    )
    
    assert response.status_code == 400
    assert "Invalid rates" in response.json["error"]

def test_update_cost_settings_partial_empty_components(client, route_with_settings):
    """Test partial update with empty components list."""
    update_data = {
        "enabled_components": []
    }
    
    response = client.patch(
        f"/api/cost/settings/{route_with_settings.id}",
        json=update_data
    )
    
    assert response.status_code == 400
    assert "one component must be enabled" in response.json["error"].lower()

def test_update_cost_settings_partial_route_not_found(client):
    """Test partial update with non-existent route."""
    update_data = {
        "rates": {
            "fuel_rate": "2.75"
        }
    }
    
    response = client.patch(
        "/api/cost/settings/00000000-0000-0000-0000-000000000000",
        json=update_data
    )
    
    assert response.status_code == 404
    assert "not found" in response.json["error"].lower()

def test_update_cost_settings_partial_invalid_decimal(client, route_with_settings):
    """Test partial update with invalid decimal format."""
    update_data = {
        "rates": {
            "fuel_rate": "invalid"
        }
    }
    
    response = client.patch(
        f"/api/cost/settings/{route_with_settings.id}",
        json=update_data
    )
    
    assert response.status_code == 400
    assert "Invalid rate value" in response.json["error"]

def test_update_cost_settings_partial_mixed_update(client, route_with_settings):
    """Test partial update with both components and rates."""
    update_data = {
        "enabled_components": ["fuel", "toll"],
        "rates": {
            "fuel_rate": "2.75"
        }
    }
    
    response = client.patch(
        f"/api/cost/settings/{route_with_settings.id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json
    assert data["enabled_components"] == ["fuel", "toll"]
    assert data["rates"]["fuel_rate"] == "2.75" 