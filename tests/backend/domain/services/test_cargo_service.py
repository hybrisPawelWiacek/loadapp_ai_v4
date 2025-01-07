"""Tests for cargo service."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4

import pytest

from backend.domain.services.cargo_service import CargoService
from backend.domain.entities.cargo import Cargo


class MockCargoRepository:
    """Mock repository for Cargo entity."""
    
    def __init__(self):
        self.cargos: Dict[UUID, Cargo] = {}
        
    def save(self, cargo: Cargo) -> Cargo:
        """Save a cargo."""
        self.cargos[cargo.id] = cargo
        return cargo
        
    def find_by_id(self, id: UUID) -> Optional[Cargo]:
        """Find a cargo by ID."""
        return self.cargos.get(id)


class MockBusinessRepository:
    """Mock repository for Business entity."""
    
    def __init__(self):
        self.businesses = {}
        
    def find_by_id(self, id: UUID) -> Optional[Dict]:
        """Find a business by ID."""
        return self.businesses.get(id)
        
    def add_business(self, id: UUID, is_active: bool = True):
        """Add a business for testing."""
        self.businesses[id] = {
            "id": id,
            "is_active": is_active
        }


class MockRouteService:
    """Mock route service."""
    
    def __init__(self):
        self.status_changes = []
        
    def handle_cargo_status_change(self, cargo_id: UUID, new_status: str):
        """Record cargo status change."""
        self.status_changes.append({
            "cargo_id": cargo_id,
            "new_status": new_status
        })


@pytest.fixture
def cargo_repository():
    """Create a mock cargo repository."""
    return MockCargoRepository()


@pytest.fixture
def business_repository():
    """Create a mock business repository."""
    return MockBusinessRepository()


@pytest.fixture
def route_service():
    """Create a mock route service."""
    return MockRouteService()


@pytest.fixture
def cargo_service(cargo_repository, business_repository, route_service):
    """Create a cargo service with mock dependencies."""
    return CargoService(cargo_repository, business_repository, route_service)


@pytest.fixture
def sample_cargo():
    """Create a sample cargo entity."""
    return Cargo(
        id=uuid4(),
        business_entity_id=uuid4(),
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value=Decimal("25000.00"),
        special_requirements=["temperature_controlled"],
        status="pending"
    )


def test_create_cargo_success(cargo_service, sample_cargo, business_repository):
    """Test successful cargo creation."""
    # Arrange
    business_repository.add_business(sample_cargo.business_entity_id)
    
    # Act
    created_cargo = cargo_service.create_cargo(sample_cargo)
    
    # Assert
    assert created_cargo.id == sample_cargo.id
    assert created_cargo.status == "pending"
    assert created_cargo.created_at is not None


def test_create_cargo_nonexistent_business(cargo_service, sample_cargo):
    """Test cargo creation with non-existent business."""
    with pytest.raises(ValueError, match="Business entity not found"):
        cargo_service.create_cargo(sample_cargo)


def test_create_cargo_inactive_business(cargo_service, sample_cargo, business_repository):
    """Test cargo creation with inactive business."""
    # Arrange
    business_repository.add_business(sample_cargo.business_entity_id, is_active=False)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Business entity is not active"):
        cargo_service.create_cargo(sample_cargo)


def test_update_cargo_success(cargo_service, sample_cargo, cargo_repository):
    """Test successful cargo update."""
    # Arrange
    cargo_repository.save(sample_cargo)
    updates = {
        "weight": 2000.0,
        "volume": 15.0,
        "value": Decimal("30000.00")
    }
    
    # Act
    updated_cargo = cargo_service.update_cargo(sample_cargo.id, updates)
    
    # Assert
    assert updated_cargo.weight == 2000.0
    assert updated_cargo.volume == 15.0
    assert updated_cargo.value == Decimal("30000.00")
    assert updated_cargo.updated_at is not None


def test_update_cargo_status_transition(cargo_service, sample_cargo, cargo_repository, route_service):
    """Test cargo status transition."""
    # Arrange
    cargo_repository.save(sample_cargo)
    updates = {"status": "in_transit"}
    
    # Act
    updated_cargo = cargo_service.update_cargo(sample_cargo.id, updates)
    
    # Assert
    assert updated_cargo.status == "in_transit"
    assert len(route_service.status_changes) == 1
    assert route_service.status_changes[0]["cargo_id"] == sample_cargo.id
    assert route_service.status_changes[0]["new_status"] == "in_transit"


def test_update_cargo_invalid_status_transition(cargo_service, sample_cargo, cargo_repository):
    """Test invalid cargo status transition."""
    # Arrange
    sample_cargo.status = "delivered"  # Terminal state
    cargo_repository.save(sample_cargo)
    updates = {"status": "in_transit"}
    
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid status transition"):
        cargo_service.update_cargo(sample_cargo.id, updates)


def test_delete_cargo_success(cargo_service, sample_cargo, cargo_repository):
    """Test successful cargo deletion."""
    # Arrange
    cargo_repository.save(sample_cargo)
    
    # Act
    result = cargo_service.delete_cargo(sample_cargo.id)
    
    # Assert
    assert result is True
    deleted_cargo = cargo_repository.find_by_id(sample_cargo.id)
    assert deleted_cargo.is_active is False


def test_delete_cargo_in_transit(cargo_service, sample_cargo, cargo_repository):
    """Test deleting cargo in transit."""
    # Arrange
    sample_cargo.status = "in_transit"
    cargo_repository.save(sample_cargo)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot delete cargo in transit"):
        cargo_service.delete_cargo(sample_cargo.id)


def test_handle_offer_finalization(cargo_service, sample_cargo, cargo_repository, route_service):
    """Test successful offer finalization."""
    # Arrange
    cargo_repository.save(sample_cargo)
    offer_id = uuid4()
    
    # Act
    cargo_service.handle_offer_finalization(sample_cargo.id, offer_id)
    
    # Assert
    updated_cargo = cargo_repository.find_by_id(sample_cargo.id)
    assert updated_cargo.status == "in_transit"
    assert len(route_service.status_changes) == 1
    assert route_service.status_changes[0]["cargo_id"] == sample_cargo.id
    assert route_service.status_changes[0]["new_status"] == "in_transit"


def test_handle_offer_finalization_invalid_state(cargo_service, sample_cargo, cargo_repository):
    """Test offer finalization with invalid cargo state."""
    # Arrange
    sample_cargo.status = "in_transit"
    cargo_repository.save(sample_cargo)
    offer_id = uuid4()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cargo must be in pending state"):
        cargo_service.handle_offer_finalization(sample_cargo.id, offer_id)


def test_get_cargo(cargo_service, sample_cargo, cargo_repository):
    """Test getting cargo by ID."""
    # Arrange
    cargo_repository.save(sample_cargo)
    
    # Act
    found_cargo = cargo_service.get_cargo(sample_cargo.id)
    
    # Assert
    assert found_cargo is not None
    assert found_cargo.id == sample_cargo.id


def test_get_nonexistent_cargo(cargo_service):
    """Test getting non-existent cargo."""
    # Act
    found_cargo = cargo_service.get_cargo(uuid4())
    
    # Assert
    assert found_cargo is None


def test_list_cargo(cargo_service):
    """Test listing cargo with pagination."""
    # Act
    result = cargo_service.list_cargo(page=1, size=10)
    
    # Assert
    assert "items" in result
    assert "total" in result
    assert "page" in result
    assert "size" in result 