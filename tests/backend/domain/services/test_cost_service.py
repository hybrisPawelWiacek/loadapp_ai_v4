"""Tests for cost service."""
import pytest
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime, timezone

from backend.domain.entities.rate_types import RateType, RateValidationSchema
from backend.domain.entities.cargo import CostSettings, CostSettingsCreate, CostBreakdown
from backend.domain.entities.transport import DriverSpecification, Transport, TruckSpecification
from backend.domain.entities.route import Route, CountrySegment, EmptyDriving
from backend.domain.entities.business import BusinessEntity
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


@pytest.fixture
def sample_route():
    """Create a sample route for testing."""
    route_id = uuid4()
    start_location_id = uuid4()
    end_location_id = uuid4()
    
    return Route(
        id=route_id,
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin_id=start_location_id,
        destination_id=end_location_id,
        pickup_time=datetime.now(),
        delivery_time=datetime.now(),
        total_distance_km=500.0,
        total_duration_hours=5.0,
        country_segments=[
            CountrySegment(
                id=uuid4(),
                route_id=route_id,
                country_code="DE",
                distance_km=200.0,
                duration_hours=2.0,
                start_location_id=start_location_id,
                end_location_id=end_location_id,
                segment_order=0
            ),
            CountrySegment(
                id=uuid4(),
                route_id=route_id,
                country_code="PL",
                distance_km=300.0,
                duration_hours=3.0,
                start_location_id=end_location_id,
                end_location_id=start_location_id,
                segment_order=1
            )
        ]
    )


@pytest.fixture
def sample_transport():
    """Create a sample transport for testing."""
    return Transport(
        id=uuid4(),
        transport_type_id="flatbed_test",
        business_entity_id=uuid4(),
        truck_specs=TruckSpecification(
            fuel_consumption_empty=25.0,
            fuel_consumption_loaded=35.0,
            toll_class="40t",
            euro_class="EURO6",
            co2_class="A",
            maintenance_rate_per_km=Decimal("0.15")
        ),
        driver_specs=DriverSpecification(
            daily_rate=Decimal("250.00"),
            driving_time_rate=Decimal("25.00"),
            required_license_type="CE",
            required_certifications=["ADR", "HAZMAT"]
        ),
        is_active=True
    )


@pytest.fixture
def sample_cost_settings():
    """Create sample cost settings for testing."""
    return CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        business_entity_id=uuid4(),
        enabled_components=["fuel", "driver", "toll", "maintenance", "overhead"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0"),
            "maintenance_rate": Decimal("0.15"),
            "toll_rate_multiplier": Decimal("1.0")
        }
    )


@pytest.fixture
def sample_business():
    """Create sample business entity for testing."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Company",
        address="123 Test Street",
        contact_info={"email": "test@example.com"},
        business_type="carrier",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],  # Operating in both countries needed for the route
        cost_overheads={"admin": Decimal("100")}
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
    assert costs["overtime_cost"] == Decimal("0.00")
    
    # Verify total cost
    assert costs["total_cost"] == Decimal("400.00")


def test_calculate_driver_costs_disabled(
    cost_service,
    route_with_long_duration,
    transport_with_driver_specs
):
    """Test driver cost calculation when disabled."""
    settings = CostSettingsCreate(
        enabled_components=["fuel"],  # At least one component must be enabled
        rates={}
    )
    
    costs = cost_service._calculate_driver_costs(
        route_with_long_duration,
        transport_with_driver_specs,
        settings
    )
    
    assert costs["total_cost"] == Decimal("0.00")


def test_calculate_driver_costs_multiple_days(
    cost_service,
    transport_with_driver_specs,
    mocker
):
    """Test driver cost calculation for multi-day route."""
    route = mocker.Mock()
    route.total_duration_hours = 36.0  # 1.5 days
    
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
    
    # Verify overtime cost (18 * 25 * 1.5)
    assert costs["overtime_cost"] == Decimal("675.00")
    
    # Verify total cost
    assert costs["total_cost"] == Decimal("1525.00")


def test_update_cost_settings_partial_success(
    cost_service,
    mock_rate_validation_repo,
    mock_settings_repo
):
    """Test partial update of cost settings."""
    route_id = uuid4()
    business_id = uuid4()
    
    # Setup existing settings
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=route_id,
        business_entity_id=business_id,
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings
    
    # Setup mock for update_settings
    updated_settings = CostSettings(
        id=existing_settings.id,
        route_id=route_id,
        business_entity_id=business_id,
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("3.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    mock_settings_repo.update_settings.return_value = updated_settings
    
    # Update only fuel rate
    updates = {
        "rates": {
            "fuel_rate": Decimal("3.0")
        }
    }
    
    updated = cost_service.update_cost_settings_partial(route_id, updates)
    
    assert updated.rates["fuel_rate"] == Decimal("3.0")
    assert updated.rates["driver_base_rate"] == Decimal("200.0")
    assert updated.enabled_components == ["fuel", "driver"]


def test_update_cost_settings_partial_invalid_rates(
    cost_service,
    mock_rate_validation_repo,
    mock_settings_repo
):
    """Test partial update with invalid rates."""
    route_id = uuid4()
    business_id = uuid4()
    
    # Setup existing settings
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=route_id,
        business_entity_id=business_id,
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings
    
    # Try to update with invalid rate
    updates = {
        "rates": {
            "fuel_rate": Decimal("10.0")  # Above max
        }
    }
    
    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings_partial(route_id, updates)
    
    assert "Invalid rates" in str(exc.value)


def test_update_cost_settings_partial_not_found(
    cost_service,
    mock_rate_validation_repo,
    mock_settings_repo
):
    """Test partial update when settings not found."""
    route_id = uuid4()
    mock_settings_repo.find_by_route_id.return_value = None
    
    updates = {
        "rates": {
            "fuel_rate": Decimal("3.0")
        }
    }
    
    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings_partial(route_id, updates)
    
    assert "Cost settings not found" in str(exc.value)


def test_update_cost_settings_partial_empty_components(
    cost_service,
    mock_rate_validation_repo,
    mock_settings_repo
):
    """Test partial update with empty components list."""
    route_id = uuid4()
    business_id = uuid4()
    
    # Setup existing settings
    existing_settings = CostSettings(
        id=uuid4(),
        route_id=route_id,
        business_entity_id=business_id,
        enabled_components=["fuel", "driver"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    mock_settings_repo.find_by_route_id.return_value = existing_settings
    
    # Setup mock for update_settings
    updated_settings = CostSettings(
        id=existing_settings.id,
        route_id=route_id,
        business_entity_id=business_id,
        enabled_components=["fuel"],
        rates={
            "fuel_rate": Decimal("2.0"),
            "driver_base_rate": Decimal("200.0")
        }
    )
    mock_settings_repo.update_settings.return_value = updated_settings
    
    # Update to empty components list
    updates = {
        "enabled_components": ["fuel"]  # At least one component must be enabled
    }
    
    updated = cost_service.update_cost_settings_partial(route_id, updates)
    
    assert updated.enabled_components == ["fuel"]
    assert updated.rates == {
        "fuel_rate": Decimal("2.0"),
        "driver_base_rate": Decimal("200.0")
    }


def test_calculate_costs_with_invalid_business_countries(
    cost_service,
    mock_settings_repo,
    mock_empty_driving_repo,
    sample_route,
    sample_transport,
    sample_cost_settings
):
    """Test cost calculation fails when business doesn't operate in required countries."""
    # Arrange
    business = BusinessEntity(
        id=uuid4(),
        name="Test Transport Company",
        address="123 Test Street",
        contact_info={"email": "test@example.com"},
        business_type="carrier",
        certifications=["ISO9001"],
        operating_countries=["DE"],  # Missing PL
        cost_overheads={"admin": Decimal("100")}
    )
    
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    mock_empty_driving_repo.find_by_id.return_value = EmptyDriving(
        id=uuid4(),
        distance_km=200,
        duration_hours=4
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match="Business entity does not operate in required countries: {'PL'}"):
        cost_service.calculate_costs(sample_route, sample_transport, business) 


def test_calculate_costs_with_valid_business(
    cost_service,
    mock_settings_repo,
    mock_empty_driving_repo,
    mock_breakdown_repo,
    mock_toll_calculator,
    sample_route,
    sample_transport,
    sample_business,
    sample_cost_settings
):
    """Test cost calculation succeeds with valid business entity."""
    # Arrange
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    mock_empty_driving_repo.find_by_id.return_value = EmptyDriving(
        id=uuid4(),
        distance_km=200,
        duration_hours=4
    )
    mock_toll_calculator.calculate_toll.return_value = Decimal("50")
    mock_breakdown_repo.save.return_value = lambda x: x
    
    # Act
    result = cost_service.calculate_costs(sample_route, sample_transport, sample_business)
    
    # Assert
    assert result is not None
    assert isinstance(result, CostBreakdown)
    assert result.route_id == sample_route.id
    assert len(result.fuel_costs) == 2  # DE and PL
    assert len(result.toll_costs) == 2  # DE and PL
    assert result.overhead_costs == Decimal("100")  # From business cost_overheads
    assert result.total_cost > 0 


def test_validate_cost_settings_success(cost_service, sample_cost_settings):
    """Test successful cost settings validation."""
    is_valid, errors = cost_service.validate_cost_settings(sample_cost_settings)
    
    assert is_valid
    assert not errors


def test_validate_cost_settings_no_components(cost_service, sample_cost_settings):
    """Test cost settings validation with no enabled components."""
    sample_cost_settings.enabled_components = []
    
    is_valid, errors = cost_service.validate_cost_settings(sample_cost_settings)
    
    assert not is_valid
    assert len(errors) == 1
    assert "At least one cost component must be enabled" in errors[0]


def test_validate_cost_settings_missing_rates(cost_service, sample_cost_settings):
    """Test cost settings validation with missing required rates."""
    sample_cost_settings.enabled_components = ["fuel", "driver"]
    sample_cost_settings.rates = {}  # Empty rates
    
    is_valid, errors = cost_service.validate_cost_settings(sample_cost_settings)
    
    assert not is_valid
    assert len(errors) == 2  # Missing fuel_rate and driver_base_rate
    assert any("fuel_rate" in error for error in errors)
    assert any("driver_base_rate" in error for error in errors)


def test_validate_cost_calculation_success(
    cost_service,
    mock_settings_repo,
    sample_cost_settings,
    sample_route
):
    """Test successful cost calculation validation."""
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    
    is_valid, errors = cost_service.validate_cost_calculation(sample_route.id)
    
    assert is_valid
    assert not errors
    mock_settings_repo.find_by_route_id.assert_called_once_with(sample_route.id)


def test_validate_cost_calculation_no_settings(
    cost_service,
    mock_settings_repo,
    sample_route
):
    """Test cost calculation validation with no settings found."""
    mock_settings_repo.find_by_route_id.return_value = None
    
    is_valid, errors = cost_service.validate_cost_calculation(sample_route.id)
    
    assert not is_valid
    assert len(errors) == 1
    assert f"No cost settings found for route {sample_route.id}" in errors[0]
    mock_settings_repo.find_by_route_id.assert_called_once_with(sample_route.id)


def test_validate_cost_calculation_invalid_settings(
    cost_service,
    mock_settings_repo,
    sample_cost_settings,
    sample_route
):
    """Test cost calculation validation with invalid settings."""
    sample_cost_settings.enabled_components = []  # Invalid: no components enabled
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    
    is_valid, errors = cost_service.validate_cost_calculation(sample_route.id)
    
    assert not is_valid
    assert len(errors) == 1
    assert "At least one cost component must be enabled" in errors[0]
    mock_settings_repo.find_by_route_id.assert_called_once_with(sample_route.id) 


def test_update_cost_settings_success(
    cost_service,
    mock_settings_repo,
    sample_cost_settings
):
    """Test successful cost settings update."""
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    mock_settings_repo.save.return_value = sample_cost_settings
    
    updates = {
        "enabled_components": ["fuel", "driver"],
        "rates": {
            "fuel_rate": "2.0",
            "driver_base_rate": "200.0"
        }
    }
    
    updated_settings = cost_service.update_cost_settings(
        route_id=sample_cost_settings.route_id,
        updates=updates
    )
    
    assert updated_settings.enabled_components == updates["enabled_components"]
    assert all(
        updated_settings.rates[k] == Decimal(v)
        for k, v in updates["rates"].items()
    )
    mock_settings_repo.save.assert_called_once()


def test_update_cost_settings_not_found(
    cost_service,
    mock_settings_repo,
    sample_cost_settings
):
    """Test cost settings update when settings not found."""
    mock_settings_repo.find_by_route_id.return_value = None
    
    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings(
            route_id=sample_cost_settings.route_id,
            updates={"enabled_components": ["fuel"]}
        )
    
    assert "Cost settings not found" in str(exc.value)


def test_update_cost_settings_invalid(
    cost_service,
    mock_settings_repo,
    sample_cost_settings
):
    """Test cost settings update with invalid settings."""
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    
    with pytest.raises(ValueError) as exc:
        cost_service.update_cost_settings(
            route_id=sample_cost_settings.route_id,
            updates={
                "enabled_components": [],  # Invalid: no components enabled
                "rates": {}
            }
        )
    
    assert "Invalid settings" in str(exc.value)
    mock_settings_repo.save.assert_not_called()


def test_get_cost_breakdown_success(
    cost_service,
    mock_breakdown_repo,
    sample_route
):
    """Test successful cost breakdown retrieval."""
    expected_breakdown = CostBreakdown(
        id=uuid4(),
        route_id=sample_route.id,
        fuel_costs={"DE": Decimal("100.0")},
        toll_costs={"DE": Decimal("50.0")},
        driver_costs=Decimal("200.0"),
        overhead_costs=Decimal("100.0"),
        timeline_event_costs={"pickup": Decimal("50.0")},
        total_cost=Decimal("500.0")
    )
    mock_breakdown_repo.find_by_route_id.return_value = expected_breakdown
    
    breakdown = cost_service.get_cost_breakdown(sample_route.id)
    
    assert breakdown == expected_breakdown
    mock_breakdown_repo.find_by_route_id.assert_called_once_with(sample_route.id)


def test_get_cost_breakdown_not_found(
    cost_service,
    mock_breakdown_repo,
    sample_route
):
    """Test cost breakdown retrieval when not found."""
    mock_breakdown_repo.find_by_route_id.return_value = None
    
    breakdown = cost_service.get_cost_breakdown(sample_route.id)
    
    assert breakdown is None
    mock_breakdown_repo.find_by_route_id.assert_called_once_with(sample_route.id)


def test_calculate_and_save_costs_success(
    cost_service,
    mock_route_repo,
    mock_transport_repo,
    mock_business_repo,
    mock_breakdown_repo,
    sample_route,
    sample_transport,
    sample_business,
    sample_cost_settings
):
    """Test successful cost calculation and saving."""
    # Setup mocks
    mock_route_repo.find_by_id.return_value = sample_route
    mock_transport_repo.find_by_id.return_value = sample_transport
    mock_business_repo.find_by_id.return_value = sample_business
    mock_breakdown_repo.save.return_value = CostBreakdown(
        id=uuid4(),
        route_id=sample_route.id,
        fuel_costs={"DE": Decimal("100.0")},
        toll_costs={"DE": Decimal("50.0")},
        driver_costs=Decimal("200.0"),
        overhead_costs=Decimal("100.0"),
        timeline_event_costs={"pickup": Decimal("50.0")},
        total_cost=Decimal("500.0")
    )
    
    # Call method
    breakdown = cost_service.calculate_and_save_costs(
        route_id=sample_route.id,
        transport_id=sample_transport.id,
        business_entity_id=sample_business.id
    )
    
    # Verify results
    assert breakdown.route_id == sample_route.id
    assert breakdown.total_cost > 0
    mock_route_repo.find_by_id.assert_called_once_with(sample_route.id)
    mock_transport_repo.find_by_id.assert_called_once_with(sample_transport.id)
    mock_business_repo.find_by_id.assert_called_once_with(sample_business.id)
    mock_breakdown_repo.save.assert_called_once()


def test_calculate_and_save_costs_validation_failed(
    cost_service,
    mock_settings_repo,
    sample_route
):
    """Test cost calculation when validation fails."""
    mock_settings_repo.find_by_route_id.return_value = None
    
    with pytest.raises(ValueError) as exc:
        cost_service.calculate_and_save_costs(
            route_id=sample_route.id,
            transport_id=uuid4(),
            business_entity_id=uuid4()
        )
    
    assert "Cost calculation validation failed" in str(exc.value)


def test_calculate_and_save_costs_entities_not_found(
    cost_service,
    mock_route_repo,
    mock_transport_repo,
    mock_business_repo,
    mock_settings_repo,
    sample_route,
    sample_cost_settings
):
    """Test cost calculation when required entities not found."""
    # Setup mocks
    mock_settings_repo.find_by_route_id.return_value = sample_cost_settings
    mock_route_repo.find_by_id.return_value = None
    mock_transport_repo.find_by_id.return_value = None
    mock_business_repo.find_by_id.return_value = None
    
    with pytest.raises(ValueError) as exc:
        cost_service.calculate_and_save_costs(
            route_id=sample_route.id,
            transport_id=uuid4(),
            business_entity_id=uuid4()
        )
    
    assert "Required entities not found" in str(exc.value) 