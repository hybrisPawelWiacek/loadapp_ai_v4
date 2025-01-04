"""Tests for cost service."""
import pytest
from decimal import Decimal
from uuid import uuid4

from backend.domain.entities.rate_types import RateType, RateValidationSchema
from backend.domain.entities.cargo import CostSettings, CostSettingsCreate
from backend.domain.entities.transport import DriverSpecification
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


@pytest.fixture
def route_with_long_duration(mocker):
    """Create a route with 12-hour duration."""
    route = mocker.Mock()
    route.total_duration_hours = 12.0
    return route


@pytest.fixture
def transport_with_driver_specs(mocker):
    """Create transport with enhanced driver specifications."""
    transport = mocker.Mock()
    transport.driver_specs = DriverSpecification(
        daily_rate=Decimal("200.00"),
        driving_time_rate=Decimal("25.00"),
        required_license_type="CE",
        required_certifications=["ADR"],
        overtime_rate_multiplier=Decimal("1.5"),
        max_driving_hours=9
    )
    return transport


def test_calculate_driver_costs_with_overtime(
    cost_service,
    route_with_long_duration,
    transport_with_driver_specs
):
    """Test driver cost calculation with overtime hours."""
    settings = CostSettingsCreate(
        enabled_components=["driver"],
        rates={}
    )
    
    costs = cost_service._calculate_driver_costs(
        route_with_long_duration,
        transport_with_driver_specs,
        settings
    )
    
    # Verify base cost (1 day)
    assert costs["base_cost"] == Decimal("200.00")
    
    # Verify regular hours cost (9 hours * 25)
    assert costs["regular_hours_cost"] == Decimal("225.00")
    
    # Verify overtime cost (3 hours * 25 * 1.5)
    assert costs["overtime_cost"] == Decimal("112.50")
    
    # Verify total cost
    assert costs["total_cost"] == Decimal("537.50")


def test_calculate_driver_costs_no_overtime(
    cost_service,
    transport_with_driver_specs,
    mocker
):
    """Test driver cost calculation without overtime."""
    route = mocker.Mock()
    route.total_duration_hours = 8.0  # Under max_driving_hours
    
    settings = CostSettingsCreate(
        enabled_components=["driver"],
        rates={}
    )
    
    costs = cost_service._calculate_driver_costs(
        route,
        transport_with_driver_specs,
        settings
    )
    
    # Verify base cost (1 day)
    assert costs["base_cost"] == Decimal("200.00")
    
    # Verify regular hours cost (8 hours * 25)
    assert costs["regular_hours_cost"] == Decimal("200.00")
    
    # Verify no overtime cost
    assert costs["overtime_cost"] == Decimal("0")
    
    # Verify total cost
    assert costs["total_cost"] == Decimal("400.00")


def test_calculate_driver_costs_disabled(
    cost_service,
    route_with_long_duration,
    transport_with_driver_specs
):
    """Test driver costs when driver component is disabled."""
    settings = CostSettingsCreate(
        enabled_components=["fuel", "toll"],  # Driver not enabled
        rates={}
    )
    
    costs = cost_service._calculate_driver_costs(
        route_with_long_duration,
        transport_with_driver_specs,
        settings
    )
    
    # All costs should be zero
    assert costs["base_cost"] == Decimal("0")
    assert costs["regular_hours_cost"] == Decimal("0")
    assert costs["overtime_cost"] == Decimal("0")
    assert costs["total_cost"] == Decimal("0")


def test_calculate_driver_costs_multiple_days(
    cost_service,
    transport_with_driver_specs,
    mocker
):
    """Test driver cost calculation for a multi-day route."""
    route = mocker.Mock()
    route.total_duration_hours = 30.0  # 1 day + 6 hours
    
    settings = CostSettingsCreate(
        enabled_components=["driver"],
        rates={}
    )
    
    costs = cost_service._calculate_driver_costs(
        route,
        transport_with_driver_specs,
        settings
    )
    
    # Verify base cost (2 days)
    assert costs["base_cost"] == Decimal("400.00")
    
    # Verify regular hours cost (18 hours * 25)
    assert costs["regular_hours_cost"] == Decimal("450.00")
    
    # Verify overtime cost (12 hours * 25 * 1.5)
    assert costs["overtime_cost"] == Decimal("450.00")
    
    # Verify total cost
    assert costs["total_cost"] == Decimal("1300.00") 


def test_update_cost_settings_partial_success(
    cost_service,
    mock_settings_repo,
    mock_rate_validation_repo
):
    """Test successful partial update of cost settings."""
    # Setup existing settings
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        business_entity_id=uuid4(),
        enabled_components=["fuel", "toll"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "toll_rate": Decimal("0.2")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings
    mock_settings_repo.update_settings.return_value = CostSettings(
        id=existing_settings.id,
        route_id=existing_settings.route_id,
        business_entity_id=existing_settings.business_entity_id,
        enabled_components=["fuel", "toll", "driver"],
        rates={
            "fuel_rate": Decimal("2.5"),
            "toll_rate": Decimal("0.2"),
            "driver_base_rate": Decimal("200.0")
        }
    )

    # Perform update
    updates = {
        "enabled_components": ["fuel", "toll", "driver"],
        "rates": {
            "fuel_rate": Decimal("2.5"),
            "driver_base_rate": Decimal("200.0")
        }
    }
    result = cost_service.update_cost_settings_partial(existing_settings.route_id, updates)

    # Verify
    assert result is not None
    assert "driver" in result.enabled_components
    assert result.rates["fuel_rate"] == Decimal("2.5")
    assert result.rates["driver_base_rate"] == Decimal("200.0")
    assert result.rates["toll_rate"] == Decimal("0.2")


def test_update_cost_settings_partial_invalid_rates(
    cost_service,
    mock_settings_repo,
    mock_rate_validation_repo
):
    """Test partial update with invalid rates."""
    # Setup existing settings
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        business_entity_id=uuid4(),
        enabled_components=["fuel", "toll"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "toll_rate": Decimal("0.2")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings

    # Attempt update with invalid rate
    updates = {
        "rates": {
            "fuel_rate": Decimal("10.0")  # Above max allowed
        }
    }

    # Verify exception is raised
    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings_partial(existing_settings.route_id, updates)
    assert "Invalid rates" in str(exc.value)


def test_update_cost_settings_partial_not_found(
    cost_service,
    mock_settings_repo
):
    """Test partial update when settings don't exist."""
    mock_settings_repo.find_by_route_id.return_value = None

    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings_partial(
            uuid4(),
            {"enabled_components": ["fuel"]}
        )
    assert "not found" in str(exc.value)


def test_update_cost_settings_partial_empty_components(
    cost_service,
    mock_settings_repo
):
    """Test partial update with empty enabled components."""
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        business_entity_id=uuid4(),
        enabled_components=["fuel", "toll"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "toll_rate": Decimal("0.2")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings

    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings_partial(
            existing_settings.route_id,
            {"enabled_components": []}
        )
    assert "one component must be enabled" in str(exc.value) 