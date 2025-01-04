"""Tests for cost service."""
import pytest
from decimal import Decimal
from uuid import uuid4

from backend.domain.entities.rate_types import RateType, RateValidationSchema
from backend.domain.entities.cargo import CostSettings, CostSettingsCreate
from backend.domain.services.cost_service import CostService


@pytest.fixture
def rate_validation_schemas():
    """Create sample rate validation schemas."""
    return {
        RateType.FUEL_RATE: RateValidationSchema(
            rate_type=RateType.FUEL_RATE,
            min_value=Decimal("0.5"),
            max_value=Decimal("5.0"),
            country_specific=True
        ),
        RateType.DRIVER_BASE_RATE: RateValidationSchema(
            rate_type=RateType.DRIVER_BASE_RATE,
            min_value=Decimal("100.0"),
            max_value=Decimal("500.0"),
            country_specific=False
        )
    }


@pytest.fixture
def mock_rate_validation_repo(mocker, rate_validation_schemas):
    """Create mock rate validation repository."""
    mock_repo = mocker.Mock()
    mock_repo.get_all_schemas.return_value = rate_validation_schemas
    return mock_repo


@pytest.fixture
def mock_settings_repo(mocker):
    """Create mock settings repository."""
    mock_repo = mocker.Mock()
    return mock_repo


@pytest.fixture
def mock_breakdown_repo(mocker):
    """Create mock breakdown repository."""
    mock_repo = mocker.Mock()
    return mock_repo


@pytest.fixture
def mock_empty_driving_repo(mocker):
    """Create mock empty driving repository."""
    mock_repo = mocker.Mock()
    return mock_repo


@pytest.fixture
def mock_toll_calculator(mocker):
    """Create mock toll calculator."""
    mock_calculator = mocker.Mock()
    return mock_calculator


@pytest.fixture
def cost_service(
    mock_settings_repo,
    mock_breakdown_repo,
    mock_empty_driving_repo,
    mock_toll_calculator,
    mock_rate_validation_repo
):
    """Create cost service with mock dependencies."""
    return CostService(
        settings_repo=mock_settings_repo,
        breakdown_repo=mock_breakdown_repo,
        empty_driving_repo=mock_empty_driving_repo,
        toll_calculator=mock_toll_calculator,
        rate_validation_repo=mock_rate_validation_repo
    )


def test_validate_rates_success(cost_service, mock_rate_validation_repo):
    """Test successful rate validation."""
    rates = {
        "fuel_rate": Decimal("2.5"),
        "driver_base_rate": Decimal("200.0")
    }
    
    is_valid, errors = cost_service.validate_rates(rates)
    
    assert is_valid
    assert not errors


def test_validate_rates_invalid_value(cost_service, mock_rate_validation_repo):
    """Test rate validation with invalid value."""
    rates = {
        "fuel_rate": Decimal("10.0"),  # Above max
        "driver_base_rate": Decimal("200.0")
    }
    
    is_valid, errors = cost_service.validate_rates(rates)
    
    assert not is_valid
    assert len(errors) == 1
    assert "fuel_rate" in errors[0]
    assert "outside allowed range" in errors[0]


def test_validate_rates_unknown_type(cost_service, mock_rate_validation_repo):
    """Test rate validation with unknown rate type."""
    rates = {
        "unknown_rate": Decimal("1.0"),
        "fuel_rate": Decimal("2.5")
    }
    
    is_valid, errors = cost_service.validate_rates(rates)
    
    assert not is_valid
    assert len(errors) == 1
    assert "Unknown rate type" in errors[0]


def test_create_cost_settings_with_invalid_rates(cost_service, mock_rate_validation_repo):
    """Test creating cost settings with invalid rates."""
    settings = CostSettingsCreate(
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("0.1")  # Below min
        }
    )
    
    with pytest.raises(ValueError) as exc:
        cost_service.create_cost_settings(
            route_id=uuid4(),
            settings=settings,
            business_entity_id=uuid4()
        )
    
    assert "Invalid rates" in str(exc.value)


def test_clone_cost_settings_with_invalid_modifications(
    cost_service,
    mock_rate_validation_repo,
    mock_settings_repo
):
    """Test cloning cost settings with invalid rate modifications."""
    source_id = uuid4()
    target_id = uuid4()
    business_id = uuid4()
    
    # Setup mock source settings
    mock_settings_repo.find_by_route_id.return_value = CostSettings(
        id=uuid4(),
        route_id=source_id,
        business_entity_id=business_id,
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    
    # Try to clone with invalid modifications
    modifications = {
        "fuel_rate": Decimal("10.0")  # Above max
    }
    
    with pytest.raises(ValueError) as exc:
        cost_service.clone_cost_settings(source_id, target_id, modifications)
    
    assert "Invalid rate modifications" in str(exc.value) 