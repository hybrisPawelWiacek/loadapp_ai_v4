"""Tests for transport API routes."""
import uuid
import pytest
from flask import Flask, g
from backend.app import create_app
from backend.infrastructure.models.transport_models import (
    TransportTypeModel,
    TruckSpecificationModel,
    DriverSpecificationModel
)


@pytest.fixture
def app(db):
    """Create Flask test app with test database session."""
    app = create_app()
    
    @app.before_request
    def before_request():
        g.db = db
    
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_transport_types(db):
    """Create sample transport types for testing."""
    # Create specifications for flatbed
    flatbed_truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    
    flatbed_driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.0",
        required_license_type="CE",
        required_certifications='["ADR"]'
    )
    
    # Create specifications for container
    container_truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=0.24,
        fuel_consumption_loaded=0.32,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="B",
        maintenance_rate_per_km="0.18"
    )
    
    container_driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="142.0",
        required_license_type="CE",
        required_certifications="[]"
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