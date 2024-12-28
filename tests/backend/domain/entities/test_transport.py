"""Tests for transport domain entities."""
import pytest
from decimal import Decimal
from uuid import UUID, uuid4

from backend.domain.entities.transport import (
    Transport,
    TransportType,
    TruckSpecification,
    DriverSpecification
)


@pytest.fixture
def sample_truck_specs():
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
def sample_driver_specs():
    """Create sample driver specifications."""
    return DriverSpecification(
        daily_rate=Decimal("250.00"),
        required_license_type="CE",
        required_certifications=["ADR", "HAZMAT"]
    )


@pytest.fixture
def sample_transport_type(sample_truck_specs, sample_driver_specs):
    """Create sample transport type."""
    return TransportType(
        id="flatbed_40t",
        name="40t Flatbed Truck",
        truck_specifications=sample_truck_specs,
        driver_specifications=sample_driver_specs
    )


def test_truck_specification_creation(sample_truck_specs):
    """Test truck specification creation."""
    assert sample_truck_specs.fuel_consumption_empty == 25.0
    assert sample_truck_specs.fuel_consumption_loaded == 35.0
    assert sample_truck_specs.toll_class == "40t"
    assert sample_truck_specs.euro_class == "EURO6"
    assert sample_truck_specs.co2_class == "A"
    assert sample_truck_specs.maintenance_rate_per_km == Decimal("0.15")


def test_driver_specification_creation(sample_driver_specs):
    """Test driver specification creation."""
    assert sample_driver_specs.daily_rate == Decimal("250.00")
    assert sample_driver_specs.required_license_type == "CE"
    assert "ADR" in sample_driver_specs.required_certifications
    assert "HAZMAT" in sample_driver_specs.required_certifications


def test_transport_type_creation(sample_transport_type, sample_truck_specs, sample_driver_specs):
    """Test transport type creation."""
    assert sample_transport_type.id == "flatbed_40t"
    assert sample_transport_type.name == "40t Flatbed Truck"
    assert sample_transport_type.truck_specifications == sample_truck_specs
    assert sample_transport_type.driver_specifications == sample_driver_specs


def test_transport_creation(sample_transport_type, sample_truck_specs, sample_driver_specs):
    """Test transport creation."""
    transport_id = uuid4()
    business_id = uuid4()
    
    transport = Transport(
        id=transport_id,
        transport_type_id=sample_transport_type.id,
        business_entity_id=business_id,
        truck_specs=sample_truck_specs,
        driver_specs=sample_driver_specs
    )
    
    assert isinstance(transport.id, UUID)
    assert transport.transport_type_id == "flatbed_40t"
    assert isinstance(transport.business_entity_id, UUID)
    assert transport.truck_specs == sample_truck_specs
    assert transport.driver_specs == sample_driver_specs
    assert transport.is_active is True


def test_transport_type_validation():
    """Test transport type validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        TransportType(
            id=123,  # Should be string
            name="Invalid Transport",
            truck_specifications=None,  # Should be TruckSpecification
            driver_specifications=None  # Should be DriverSpecification
        )


def test_truck_specification_validation():
    """Test truck specification validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        TruckSpecification(
            fuel_consumption_empty="invalid",  # Should be float
            fuel_consumption_loaded="invalid",  # Should be float
            toll_class=123,  # Should be string
            euro_class=123,  # Should be string
            co2_class=123,  # Should be string
            maintenance_rate_per_km="invalid"  # Should be Decimal
        )


def test_driver_specification_validation():
    """Test driver specification validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        DriverSpecification(
            daily_rate="invalid",  # Should be Decimal
            required_license_type=123,  # Should be string
            required_certifications="invalid"  # Should be list
        ) 