"""Tests for cargo API routes."""
import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from flask import g

from backend.infrastructure.models.cargo_models import CargoModel
from backend.infrastructure.models.business_models import BusinessEntityModel


@pytest.fixture
def sample_business(db):
    """Create a sample business entity for testing."""
    business = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Business",
        address="123 Test Street, Test City, 12345",
        contact_info={"email": "test@business.com", "phone": "+1234567890"},
        business_type="logistics",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"general": "100.00"}
    )
    db.add(business)
    db.commit()
    return business


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
        special_requirements=json.dumps(["temperature_controlled"]),
        status="pending"
    )
    db.add(cargo)
    db.commit()
    return cargo


@pytest.fixture
def sample_cargo_data(sample_business):
    """Create sample cargo data for testing."""
    return {
        "business_entity_id": str(sample_business.id),
        "weight": 1500.0,
        "volume": 10.0,
        "cargo_type": "general",
        "value": "25000.00",
        "special_requirements": ["temperature_controlled"]
    }


def test_create_cargo_success(client, sample_business, sample_cargo_data):
    """Test successful cargo creation."""
    response = client.post("/api/cargo", json=sample_cargo_data)
    assert response.status_code == 201
    
    data = response.get_json()
    assert data["business_entity_id"] == str(sample_business.id)
    assert data["weight"] == 1500.0
    assert data["volume"] == 10.0
    assert data["cargo_type"] == "general"
    assert data["value"] == "25000.00"
    assert data["special_requirements"] == ["temperature_controlled"]
    assert data["status"] == "pending"
    assert "created_at" in data
    assert data["updated_at"] is None


def test_create_cargo_invalid_data(client, sample_business):
    """Test cargo creation with invalid data."""
    # Test missing required fields
    response = client.post("/api/cargo", json={})
    assert response.status_code == 400
    assert "Missing required field" in response.get_json()["error"]
    
    # Test invalid value format
    invalid_data = {
        "business_entity_id": str(sample_business.id),
        "weight": 1500.0,
        "volume": 10.0,
        "cargo_type": "general",
        "value": "invalid",
        "special_requirements": []
    }
    response = client.post("/api/cargo", json=invalid_data)
    assert response.status_code == 400
    assert "Invalid value format" in response.get_json()["error"]
    
    # Test negative weight
    invalid_data["value"] = "25000.00"
    invalid_data["weight"] = -1
    response = client.post("/api/cargo", json=invalid_data)
    assert response.status_code == 400
    assert "Weight must be positive" in response.get_json()["error"]


def test_create_cargo_nonexistent_business(client, sample_cargo_data):
    """Test cargo creation with non-existent business entity."""
    sample_cargo_data["business_entity_id"] = str(uuid.uuid4())
    response = client.post("/api/cargo", json=sample_cargo_data)
    assert response.status_code == 404
    assert "Business entity not found" in response.get_json()["error"]


def test_get_cargo_success(client, sample_cargo):
    """Test successful cargo retrieval."""
    response = client.get(f"/api/cargo/{sample_cargo.id}")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["id"] == sample_cargo.id
    assert data["business_entity_id"] == sample_cargo.business_entity_id
    assert data["weight"] == sample_cargo.weight
    assert data["volume"] == sample_cargo.volume
    assert data["cargo_type"] == sample_cargo.cargo_type
    assert data["value"] == sample_cargo.value
    assert data["special_requirements"] == sample_cargo.get_special_requirements()
    assert data["status"] == sample_cargo.status


def test_get_cargo_not_found(client):
    """Test cargo retrieval with invalid ID."""
    response = client.get(f"/api/cargo/{uuid.uuid4()}")
    assert response.status_code == 404
    assert "Cargo not found" in response.get_json()["error"]


def test_update_cargo_success(client, sample_cargo):
    """Test successful cargo update."""
    update_data = {
        "weight": 2000.0,
        "volume": 15.0,
        "value": "30000.00"
    }
    
    response = client.put(f"/api/cargo/{sample_cargo.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["id"] == sample_cargo.id
    assert data["weight"] == 2000.0
    assert data["volume"] == 15.0
    assert data["value"] == "30000.00"
    assert "updated_at" in data


def test_update_cargo_in_transit(client, sample_cargo, db):
    """Test updating cargo that is in transit."""
    # Set cargo to in_transit
    sample_cargo.status = "in_transit"
    db.commit()
    
    update_data = {"weight": 2000.0}
    response = client.put(f"/api/cargo/{sample_cargo.id}", json=update_data)
    assert response.status_code == 409
    assert "Cannot update cargo in transit" in response.get_json()["error"]


def test_list_cargo_pagination(client, db, sample_business):
    """Test cargo listing with pagination."""
    # Create multiple cargo entries
    for i in range(15):
        cargo = CargoModel(
            id=str(uuid.uuid4()),
            business_entity_id=sample_business.id,
            weight=1000.0 + i,
            volume=10.0,
            cargo_type="general",
            value=str(Decimal("25000.00")),
            special_requirements=[],
            status="pending"
        )
        db.add(cargo)
    db.commit()
    
    # Test default pagination (page 1, size 10)
    response = client.get("/api/cargo")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["items"]) == 10
    assert data["total"] > 10
    assert data["page"] == 1
    assert data["size"] == 10
    
    # Test custom page size
    response = client.get("/api/cargo?page=2&size=5")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["items"]) == 5
    assert data["page"] == 2
    assert data["size"] == 5


def test_list_cargo_business_filter(client, db, sample_business):
    """Test cargo listing with business entity filter."""
    response = client.get(f"/api/cargo?business_entity_id={sample_business.id}")
    assert response.status_code == 200
    
    data = response.get_json()
    for item in data["items"]:
        assert item["business_entity_id"] == str(sample_business.id)


def test_delete_cargo_success(client, sample_cargo):
    """Test successful cargo deletion."""
    response = client.delete(f"/api/cargo/{sample_cargo.id}")
    assert response.status_code == 204


def test_delete_cargo_in_transit(client, sample_cargo, db):
    """Test deleting cargo that is in transit."""
    # Set cargo to in_transit
    sample_cargo.status = "in_transit"
    db.commit()
    
    response = client.delete(f"/api/cargo/{sample_cargo.id}")
    assert response.status_code == 409
    assert "Cannot delete cargo in transit" in response.get_json()["error"]


def test_get_cargo_status_history_empty(client, sample_cargo):
    """Test getting cargo status history when no changes have been made."""
    response = client.get(f"/api/cargo/{sample_cargo.id}/status-history")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["cargo_id"] == str(sample_cargo.id)
    assert data["current_status"] == sample_cargo.status
    assert data["history"] == []


def test_get_cargo_status_history_after_update(client, sample_cargo, db):
    """Test getting cargo status history after status update."""
    # First update the cargo status
    update_response = client.put(
        f"/api/cargo/{sample_cargo.id}",
        json={"status": "in_transit"}
    )
    assert update_response.status_code == 200
    
    # Then get the history
    history_response = client.get(f"/api/cargo/{sample_cargo.id}/status-history")
    assert history_response.status_code == 200
    
    data = history_response.get_json()
    assert data["cargo_id"] == str(sample_cargo.id)
    assert data["current_status"] == "in_transit"
    assert len(data["history"]) == 1
    
    history_entry = data["history"][0]
    assert history_entry["old_status"] == "pending"
    assert history_entry["new_status"] == "in_transit"
    assert history_entry["trigger"] == "manual_update"
    assert "timestamp" in history_entry
    assert "details" in history_entry


def test_get_cargo_status_history_not_found(client):
    """Test getting status history for non-existent cargo."""
    response = client.get(f"/api/cargo/{uuid.uuid4()}/status-history")
    assert response.status_code == 404
    assert "Cargo not found" in response.get_json()["error"] 