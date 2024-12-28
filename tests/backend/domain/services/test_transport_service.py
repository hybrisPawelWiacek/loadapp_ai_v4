"""Tests for transport service."""
import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from typing import List, Optional

from backend.domain.services.transport_service import TransportService
from backend.domain.entities.transport import (
    Transport,
    TransportType,
    TruckSpecification,
    DriverSpecification
)
from backend.domain.entities.business import BusinessEntity


class MockTransportRepository:
    """Mock repository for Transport entity."""
    
    def __init__(self):
        self.transports = {}
        
    def save(self, transport: Transport) -> Transport:
        """Save a transport instance."""
        self.transports[transport.id] = transport
        return transport
        
    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find a transport by ID."""
        return self.transports.get(id)


class MockTransportTypeRepository:
    """Mock repository for TransportType entity."""
    
    def __init__(self):
        self.transport_types = {}
        
    def find_by_id(self, id: str) -> Optional[TransportType]:
        """Find a transport type by ID."""
        return self.transport_types.get(id)
        
    def list_all(self) -> List[TransportType]:
        """List all available transport types."""
        return list(self.transport_types.values())


@pytest.fixture
def truck_specs() -> TruckSpecification:
    """Create sample truck specifications."""
    return TruckSpecification(
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=35.0,
        toll_class="40t",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km=Decimal("0.15")
    )


@pytest.fixture
def driver_specs() -> DriverSpecification:
    """Create sample driver specifications."""
    return DriverSpecification(
        daily_rate=Decimal("250.00"),
        required_license_type="CE",
        required_certifications=["ADR", "HAZMAT"]
    )


@pytest.fixture
def transport_type(truck_specs, driver_specs) -> TransportType:
    """Create sample transport type."""
    return TransportType(
        id="flatbed_40t",
        name="40t Flatbed Truck",
        truck_specifications=truck_specs,
        driver_specifications=driver_specs
    )


@pytest.fixture
def transport_repo() -> MockTransportRepository:
    """Create mock transport repository."""
    return MockTransportRepository()


@pytest.fixture
def transport_type_repo(transport_type) -> MockTransportTypeRepository:
    """Create mock transport type repository with sample data."""
    repo = MockTransportTypeRepository()
    repo.transport_types[transport_type.id] = transport_type
    return repo


@pytest.fixture
def transport_service(transport_repo, transport_type_repo) -> TransportService:
    """Create transport service with mock repositories."""
    return TransportService(
        transport_repo=transport_repo,
        transport_type_repo=transport_type_repo
    )


@pytest.fixture
def business_entity() -> BusinessEntity:
    """Create sample business entity."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Co.",
        certifications=["ISO9001", "ADR"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": Decimal("100.00")}
    )


def test_create_transport_success(transport_service, business_entity):
    """Test successful transport creation."""
    # Act
    transport = transport_service.create_transport(
        transport_type_id="flatbed_40t",
        business_entity_id=business_entity.id
    )
    
    # Assert
    assert transport is not None
    assert isinstance(transport.id, UUID)
    assert transport.transport_type_id == "flatbed_40t"
    assert transport.business_entity_id == business_entity.id
    assert transport.is_active is True
    assert transport.truck_specs.toll_class == "40t"
    assert transport.driver_specs.daily_rate == Decimal("250.00")


def test_create_transport_nonexistent_type(transport_service, business_entity):
    """Test transport creation with nonexistent transport type."""
    # Act
    transport = transport_service.create_transport(
        transport_type_id="nonexistent",
        business_entity_id=business_entity.id
    )
    
    # Assert
    assert transport is None


def test_get_transport_success(transport_service, business_entity):
    """Test successful transport retrieval."""
    # Arrange
    transport = transport_service.create_transport(
        transport_type_id="flatbed_40t",
        business_entity_id=business_entity.id
    )
    
    # Act
    retrieved = transport_service.get_transport(transport.id)
    
    # Assert
    assert retrieved is not None
    assert retrieved.id == transport.id
    assert retrieved.transport_type_id == transport.transport_type_id
    assert retrieved.business_entity_id == transport.business_entity_id


def test_get_transport_nonexistent(transport_service):
    """Test transport retrieval with nonexistent ID."""
    # Act
    transport = transport_service.get_transport(uuid4())
    
    # Assert
    assert transport is None


def test_list_transport_types(transport_service, transport_type):
    """Test listing all transport types."""
    # Act
    types = transport_service.list_transport_types()
    
    # Assert
    assert len(types) == 1
    assert types[0] == transport_type


def test_validate_transport_for_business(transport_service, business_entity):
    """Test transport validation for business (always returns True in PoC)."""
    # Arrange
    transport = transport_service.create_transport(
        transport_type_id="flatbed_40t",
        business_entity_id=business_entity.id
    )
    
    # Act
    is_valid = transport_service.validate_transport_for_business(
        transport=transport,
        business=business_entity
    )
    
    # Assert
    assert is_valid is True 