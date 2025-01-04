"""Tests for toll rate adapter."""
import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from backend.domain.entities.route import CountrySegment, Location
from backend.domain.entities.transport import TollRateOverride
from backend.infrastructure.adapters.toll_rate_adapter import TollRateAdapter
from backend.infrastructure.external_services.toll_rate_service import TollRateService
from backend.infrastructure.repositories.toll_rate_override_repository import TollRateOverrideRepository


@pytest.fixture
def sample_segment():
    """Create a sample route segment."""
    return CountrySegment(
        id=uuid4(),
        route_id=uuid4(),
        country_code="DE",
        distance_km=100.0,
        duration_hours=1.5,
        start_location_id=uuid4(),
        end_location_id=uuid4(),
        segment_order=0
    )


@pytest.fixture
def sample_truck_specs():
    """Create sample truck specifications."""
    return {
        "toll_class": "4",  # Class 4 (over 18t)
        "euro_class": "VI",  # EURO VI
        "co2_class": "A"
    }


@pytest.fixture
def mock_toll_service():
    """Create a mock toll rate service."""
    service = Mock(spec=TollRateService)
    service.get_toll_rate.return_value = Decimal("24.80")  # Base rate for test
    return service


@pytest.fixture
def mock_override_repo():
    """Create a mock override repository."""
    repo = Mock(spec=TollRateOverrideRepository)
    return repo


def test_calculate_toll_without_override(
    sample_segment,
    sample_truck_specs,
    mock_toll_service,
    mock_override_repo
):
    """Test toll calculation without any overrides."""
    adapter = TollRateAdapter(mock_toll_service, mock_override_repo)
    
    toll = adapter.calculate_toll(sample_segment, sample_truck_specs)
    
    assert toll == Decimal("24.80")
    mock_toll_service.get_toll_rate.assert_called_once_with(
        country_code="DE",
        distance_km=100.0,
        toll_class="4",
        euro_class="VI",
        co2_class="A"
    )
    mock_override_repo.find_for_business.assert_not_called()


def test_calculate_toll_with_override(
    sample_segment,
    sample_truck_specs,
    mock_toll_service,
    mock_override_repo
):
    """Test toll calculation with an override."""
    business_id = uuid4()
    
    # Setup mock override
    override = TollRateOverride(
        id=uuid4(),
        vehicle_class="4",
        rate_multiplier=Decimal("1.25"),
        country_code="DE",
        business_entity_id=business_id
    )
    mock_override_repo.find_for_business.return_value = override
    
    adapter = TollRateAdapter(mock_toll_service, mock_override_repo)
    
    toll = adapter.calculate_toll(
        sample_segment,
        sample_truck_specs,
        business_entity_id=business_id,
        overrides={"vehicle_class": "4"}
    )
    
    # Base toll (24.80) * multiplier (1.25) = 31.00
    assert toll == Decimal("31.00")
    
    mock_override_repo.find_for_business.assert_called_once_with(
        business_entity_id=business_id,
        country_code="DE",
        vehicle_class="4"
    )


def test_calculate_toll_override_not_found(
    sample_segment,
    sample_truck_specs,
    mock_toll_service,
    mock_override_repo
):
    """Test toll calculation when override is not found."""
    business_id = uuid4()
    
    # Setup mock to return None (no override found)
    mock_override_repo.find_for_business.return_value = None
    
    adapter = TollRateAdapter(mock_toll_service, mock_override_repo)
    
    toll = adapter.calculate_toll(
        sample_segment,
        sample_truck_specs,
        business_entity_id=business_id,
        overrides={"vehicle_class": "4"}
    )
    
    # Should return base toll without multiplier
    assert toll == Decimal("24.80")
    
    mock_override_repo.find_for_business.assert_called_once_with(
        business_entity_id=business_id,
        country_code="DE",
        vehicle_class="4"
    ) 