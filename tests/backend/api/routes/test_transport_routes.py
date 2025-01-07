"""Tests for transport-related API routes."""
import json
import uuid
import pytest
from flask import Flask, g

from backend.api.routes.transport_routes import transport_bp
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.business_models import BusinessEntityModel


@pytest.fixture
def app(db):
    """Create Flask test app with transport routes."""
    app = Flask(__name__)
    app.register_blueprint(transport_bp)
    
    # Add database to app context
    @app.before_request
    def before_request():
        g.db = db
    
    return app


@pytest.fixture
def sample_business(db):
    """Create a sample business entity."""
    business = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Transport Co",
        address="Test Address",
        contact_info={"email": "test@example.com"},
        business_type="TRANSPORT",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": "100.00"}
    )
    db.add(business)
    db.commit()
    return business


@pytest.fixture
def sample_transport_types(db):
    """Create sample transport types with specifications."""
    # Create truck specifications
    flatbed_truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    
    container_truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.25,
        fuel_consumption_loaded=0.32,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="B",
        maintenance_rate_per_km="0.18"
    )
    
    # Create driver specifications
    flatbed_driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.0",
        driving_time_rate="25.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    
    container_driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="142.0",
        driving_time_rate="27.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR", "HACCP"])
    )
    
    # Create transport types
    types = [
        TransportTypeModel(
            id="flatbed",
            name="Flatbed",
            truck_specifications=flatbed_truck_spec,
            driver_specifications=flatbed_driver_spec
        ),
        TransportTypeModel(
            id="container",
            name="Container",
            truck_specifications=container_truck_spec,
            driver_specifications=container_driver_spec
        )
    ]
    
    # Add all objects to session
    db.add(flatbed_truck_spec)
    db.add(flatbed_driver_spec)
    db.add(container_truck_spec)
    db.add(container_driver_spec)
    
    for t in types:
        db.add(t)
    
    db.commit()
    
    return types  # Using transaction rollback from conftest.py


@pytest.fixture
def sample_transports(db, sample_business, sample_transport_types):
    """Create sample transports for testing."""
    transports = []
    
    # Create 2 transports of each type
    for transport_type in sample_transport_types:
        for _ in range(2):
            transport = TransportModel(
                id=str(uuid.uuid4()),
                transport_type_id=transport_type.id,
                business_entity_id=sample_business.id,
                truck_specifications_id=transport_type.truck_specifications_id,
                driver_specifications_id=transport_type.driver_specifications_id,
                is_active=True
            )
            transports.append(transport)
            db.add(transport)
    
    # Add one inactive transport
    inactive_transport = TransportModel(
        id=str(uuid.uuid4()),
        transport_type_id=sample_transport_types[0].id,
        business_entity_id=sample_business.id,
        truck_specifications_id=sample_transport_types[0].truck_specifications_id,
        driver_specifications_id=sample_transport_types[0].driver_specifications_id,
        is_active=False
    )
    transports.append(inactive_transport)
    db.add(inactive_transport)
    
    db.commit()
    return transports


def test_list_transport_types(client, sample_transport_types):
    """Test GET /api/transport/types endpoint."""
    response = client.get("/api/transport/types")
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["id"] == "flatbed"
    assert data[1]["id"] == "container"
    
    # Verify structure of response
    flatbed = data[0]
    assert flatbed["name"] == "Flatbed"
    assert "truck_specifications" in flatbed
    assert "driver_specifications" in flatbed
    assert flatbed["truck_specifications"]["fuel_consumption_empty"] == 0.22


def test_get_transport_type(client, sample_transport_types):
    """Test GET /api/transport/types/<type_id> endpoint."""
    response = client.get("/api/transport/types/flatbed")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["id"] == "flatbed"
    assert data["name"] == "Flatbed"
    assert data["truck_specifications"]["toll_class"] == "euro6"
    assert "ADR" in data["driver_specifications"]["required_certifications"]


def test_get_nonexistent_transport_type(client):
    """Test GET /api/transport/types/<type_id> with invalid ID."""
    response = client.get("/api/transport/types/nonexistent")
    assert response.status_code == 404
    
    data = response.get_json()
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_list_business_transports(client, sample_business, sample_transports):
    """Test GET /api/transport/business/<business_id> endpoint."""
    response = client.get(f"/api/transport/business/{sample_business.id}")
    assert response.status_code == 200
    
    data = response.get_json()
    # Should return 4 active transports (2 of each type)
    assert len(data) == 4
    
    # Verify structure of response
    transport = data[0]
    assert "id" in transport
    assert "transport_type_id" in transport
    assert "business_entity_id" in transport
    assert "truck_specifications" in transport
    assert "driver_specifications" in transport
    assert transport["is_active"] is True
    
    # Verify truck specifications
    truck_specs = transport["truck_specifications"]
    assert "fuel_consumption_empty" in truck_specs
    assert "fuel_consumption_loaded" in truck_specs
    assert "toll_class" in truck_specs
    assert "euro_class" in truck_specs
    assert "co2_class" in truck_specs
    assert "maintenance_rate_per_km" in truck_specs
    
    # Verify driver specifications
    driver_specs = transport["driver_specifications"]
    assert "daily_rate" in driver_specs
    assert "driving_time_rate" in driver_specs
    assert "required_license_type" in driver_specs
    assert "required_certifications" in driver_specs


def test_list_business_transports_invalid_id(client):
    """Test GET /api/transport/business/<business_id> with invalid business ID."""
    response = client.get("/api/transport/business/invalid-uuid")
    assert response.status_code == 400
    
    data = response.get_json()
    assert "error" in data
    assert "Invalid business ID format" in data["error"]


def test_list_business_transports_nonexistent_business(client):
    """Test GET /api/transport/business/<business_id> with nonexistent business ID."""
    response = client.get(f"/api/transport/business/{uuid.uuid4()}")
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 0  # Should return empty list for nonexistent business 