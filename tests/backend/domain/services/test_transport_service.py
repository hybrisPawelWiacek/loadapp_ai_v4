"""Tests for transport service."""
import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from typing import List, Optional
from unittest.mock import Mock

from backend.domain.services.transport_service import TransportService
from backend.domain.entities.transport import (
    Transport,
    TransportType,
    TruckSpecification,
    DriverSpecification
)
from backend.domain.entities.business import BusinessEntity
from backend.domain.services.business_service import BusinessService


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
    """Create test truck specifications."""
    return TruckSpecification(
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km=Decimal("0.15")
    )


@pytest.fixture
def driver_specs() -> DriverSpecification:
    """Create test driver specifications."""
    return DriverSpecification(
        daily_rate=Decimal("138.0"),
        driving_time_rate=Decimal("25.00"),
        required_license_type="CE",
        required_certifications=["ADR"]
    )


@pytest.fixture
def transport_type(truck_specs, driver_specs) -> TransportType:
    """Create test transport type."""
    return TransportType(
        id="flatbed",
        name="Flatbed",
        truck_specifications=truck_specs,
        driver_specifications=driver_specs
    )


@pytest.fixture
def transport_repo() -> MockTransportRepository:
    """Create mock transport repository."""
    return MockTransportRepository()


@pytest.fixture
def transport_type_repo(transport_type) -> MockTransportTypeRepository:
    """Create mock transport type repository with test data."""
    repo = MockTransportTypeRepository()
    repo.transport_types[transport_type.id] = transport_type
    return repo


@pytest.fixture
def business_service() -> Mock:
    """Create mock business service."""
    service = Mock(spec=BusinessService)
    service.validate_business_for_route.return_value = True
    return service


@pytest.fixture
def transport_service(transport_repo, transport_type_repo, business_service) -> TransportService:
    """Create transport service with mock dependencies."""
    return TransportService(
        transport_repo=transport_repo,
        transport_type_repo=transport_type_repo,
        business_service=business_service
    )


@pytest.fixture
def business_entity() -> BusinessEntity:
    """Create test business entity."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info={"email": "test@example.com", "phone": "+49123456789"},
        business_type="TRANSPORT_COMPANY",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": Decimal("100.00")},
        is_active=True
    )


@pytest.fixture
def valid_transport(transport_type, business_entity) -> Transport:
    """Create a valid transport instance for testing."""
    return Transport(
        id=uuid4(),
        transport_type_id=transport_type.id,
        business_entity_id=business_entity.id,
        truck_specs=transport_type.truck_specifications,
        driver_specs=transport_type.driver_specifications,
        is_active=True
    )


def test_create_transport_success(transport_service, business_entity):
    """Test successful transport creation."""
    transport = transport_service.create_transport(
        transport_type_id="flatbed",
        business_entity_id=business_entity.id
    )
    
    assert transport is not None
    assert transport.transport_type_id == "flatbed"
    assert transport.business_entity_id == business_entity.id
    assert transport.is_active is True


def test_create_transport_nonexistent_type(transport_service, business_entity):
    """Test transport creation with nonexistent type."""
    transport = transport_service.create_transport(
        transport_type_id="nonexistent",
        business_entity_id=business_entity.id
    )
    
    assert transport is None


def test_get_transport_success(transport_service, business_entity):
    """Test successful transport retrieval."""
    transport = transport_service.create_transport(
        transport_type_id="flatbed",
        business_entity_id=business_entity.id
    )
    
    retrieved = transport_service.get_transport(transport.id)
    assert retrieved is not None
    assert retrieved.id == transport.id


def test_get_transport_nonexistent(transport_service):
    """Test transport retrieval with nonexistent ID."""
    transport = transport_service.get_transport(uuid4())
    assert transport is None


def test_list_transport_types(transport_service, transport_type):
    """Test listing available transport types."""
    types = transport_service.list_transport_types()
    assert len(types) == 1
    assert types[0].id == transport_type.id


def test_validate_transport_for_business(transport_service, business_entity):
    """Test transport validation for business entity."""
    transport = transport_service.create_transport(
        transport_type_id="flatbed",
        business_entity_id=business_entity.id
    )
    
    is_valid = transport_service.validate_transport_for_business(
        transport=transport,
        business=business_entity,
        route_countries=["DE", "PL"]
    )
    
    assert is_valid is True


def test_validate_transport_for_business_valid(
    transport_service: TransportService,
    valid_transport: Transport,
    business_entity: BusinessEntity,
    business_service: Mock
):
    """Test successful transport validation for business."""
    business_service.validate_business_for_route.return_value = True
    
    is_valid = transport_service.validate_transport_for_business(
        transport=valid_transport,
        business=business_entity,
        route_countries=["DE", "PL"]
    )
    
    assert is_valid is True
    business_service.validate_business_for_route.assert_called_once_with(
        business_entity, ["DE", "PL"]
    )


def test_validate_transport_for_business_invalid(
    transport_service: TransportService,
    valid_transport: Transport,
    business_entity: BusinessEntity,
    business_service: Mock
):
    """Test failed transport validation for business."""
    business_service.validate_business_for_route.return_value = False
    
    is_valid = transport_service.validate_transport_for_business(
        transport=valid_transport,
        business=business_entity,
        route_countries=["DE", "PL"]
    )
    
    assert is_valid is False
    business_service.validate_business_for_route.assert_called_once_with(
        business_entity, ["DE", "PL"]
    ) 