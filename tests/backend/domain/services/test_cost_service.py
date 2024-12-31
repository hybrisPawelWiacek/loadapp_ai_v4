"""Tests for cost service."""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from backend.domain.services.cost_service import CostService
from backend.domain.entities.cargo import CostSettings, CostBreakdown
from backend.domain.entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving
)
from backend.domain.entities.transport import (
    Transport, TruckSpecification,
    DriverSpecification
)
from backend.domain.entities.business import BusinessEntity


class MockCostSettingsRepository:
    """Mock repository for CostSettings entity."""
    
    def __init__(self):
        self.settings = {}
        
    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings."""
        self.settings[settings.route_id] = settings
        return settings
        
    def find_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Find cost settings by route ID."""
        return self.settings.get(route_id)


class MockCostBreakdownRepository:
    """Mock repository for CostBreakdown entity."""
    
    def __init__(self):
        self.breakdowns = {}
        
    def save(self, breakdown: CostBreakdown) -> CostBreakdown:
        """Save cost breakdown."""
        self.breakdowns[breakdown.route_id] = breakdown
        return breakdown
        
    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find cost breakdown by route ID."""
        return self.breakdowns.get(route_id)


class MockEmptyDrivingRepository:
    """Mock repository for EmptyDriving entity."""
    
    def __init__(self):
        self.empty_drivings = {}
        
    def save(self, empty_driving: EmptyDriving) -> EmptyDriving:
        """Save empty driving."""
        self.empty_drivings[empty_driving.id] = empty_driving
        return empty_driving
        
    def find_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving by ID."""
        return self.empty_drivings.get(id)


class MockTollCalculator:
    """Mock toll calculator."""
    
    def calculate_toll(
        self,
        segment: CountrySegment,
        truck_specs: dict
    ) -> Decimal:
        """Calculate toll costs for a country segment."""
        # Return mock toll rates based on country and distance
        rates = {
            "DE": Decimal("0.187"),  # EUR/km for Germany
            "PL": Decimal("0.095")   # EUR/km for Poland
        }
        rate = rates.get(segment.country_code, Decimal("0.15"))
        return rate * Decimal(str(segment.distance_km))


@pytest.fixture
def empty_driving() -> EmptyDriving:
    """Create sample empty driving segment."""
    return EmptyDriving(
        id=uuid4(),
        distance_km=200.0,
        duration_hours=4.0
    )


@pytest.fixture
def empty_driving_repo(empty_driving) -> MockEmptyDrivingRepository:
    """Create mock empty driving repository."""
    repo = MockEmptyDrivingRepository()
    repo.save(empty_driving)
    return repo


@pytest.fixture
def settings_repo() -> MockCostSettingsRepository:
    """Create mock cost settings repository."""
    return MockCostSettingsRepository()


@pytest.fixture
def breakdown_repo() -> MockCostBreakdownRepository:
    """Create mock cost breakdown repository."""
    return MockCostBreakdownRepository()


@pytest.fixture
def toll_calculator() -> MockTollCalculator:
    """Create mock toll calculator."""
    return MockTollCalculator()


@pytest.fixture
def cost_service(
    settings_repo,
    breakdown_repo,
    empty_driving_repo,
    toll_calculator
) -> CostService:
    """Create cost service with mock dependencies."""
    return CostService(
        settings_repo=settings_repo,
        breakdown_repo=breakdown_repo,
        empty_driving_repo=empty_driving_repo,
        toll_calculator=toll_calculator
    )


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
def transport(truck_specs, driver_specs) -> Transport:
    """Create sample transport."""
    return Transport(
        id=uuid4(),
        transport_type_id=str(uuid4()),
        business_entity_id=uuid4(),
        truck_specs=truck_specs,
        driver_specs=driver_specs,
        is_active=True
    )


@pytest.fixture
def business_entity() -> BusinessEntity:
    """Create sample business entity."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info={
            "email": "test@example.com",
            "phone": "+49123456789"
        },
        business_type="TRANSPORT_COMPANY",
        certifications=["ISO9001", "ADR"],
        operating_countries=["DE", "PL"],
        cost_overheads={
            "admin": Decimal("100.00"),
            "insurance": Decimal("150.00")
        }
    )


@pytest.fixture
def route(empty_driving) -> Route:
    """Create sample route."""
    berlin = Location(
        id=uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin, Germany"
    )
    frankfurt = Location(
        id=uuid4(),
        latitude=50.110924,
        longitude=8.682127,
        address="Frankfurt, Germany"
    )
    warsaw = Location(
        id=uuid4(),
        latitude=52.237049,
        longitude=21.017532,
        address="Warsaw, Poland"
    )
    
    timeline_events = [
        TimelineEvent(
            id=uuid4(),
            type="pickup",
            location=berlin,
            planned_time=datetime.now(timezone.utc),
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEvent(
            id=uuid4(),
            type="rest",
            location=frankfurt,
            planned_time=datetime.now(timezone.utc) + timedelta(hours=4),
            duration_hours=1.0,
            event_order=2
        ),
        TimelineEvent(
            id=uuid4(),
            type="delivery",
            location=warsaw,
            planned_time=datetime.now(timezone.utc) + timedelta(hours=8),
            duration_hours=1.0,
            event_order=3
        )
    ]
    
    country_segments = [
        CountrySegment(
            country_code="DE",
            distance_km=200.0,
            duration_hours=2.0,
            start_location=berlin,
            end_location=frankfurt
        ),
        CountrySegment(
            country_code="PL",
            distance_km=300.0,
            duration_hours=3.0,
            start_location=frankfurt,
            end_location=warsaw
        )
    ]
    
    return Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin_id=berlin.id,
        destination_id=warsaw.id,
        pickup_time=timeline_events[0].planned_time,
        delivery_time=timeline_events[-1].planned_time,
        empty_driving_id=empty_driving.id,
        timeline_events=timeline_events,
        country_segments=country_segments,
        total_distance_km=700.0,
        total_duration_hours=9.0,
        is_feasible=True
    )


def test_create_cost_settings_success(cost_service):
    """Test successful cost settings creation."""
    # Arrange
    route_id = uuid4()
    business_entity_id = uuid4()
    enabled_components = ["fuel", "toll", "driver", "overhead"]
    rates = {
        "fuel_rate": Decimal("1.85"),
        "event_rate": Decimal("50.00")
    }
    
    # Act
    settings = cost_service.create_cost_settings(
        route_id=route_id,
        business_entity_id=business_entity_id,
        enabled_components=enabled_components,
        rates=rates
    )
    
    # Assert
    assert settings is not None
    assert isinstance(settings.id, UUID)
    assert settings.route_id == route_id
    assert settings.business_entity_id == business_entity_id
    assert settings.enabled_components == enabled_components
    assert settings.rates == rates


def test_calculate_costs_all_components(
    cost_service,
    route,
    transport,
    business_entity
):
    """Test cost calculation with all components enabled."""
    # Arrange
    # Update route duration to 30 hours to ensure 2 days of driver costs
    route.total_duration_hours = 30.0
    
    settings = cost_service.create_cost_settings(
        route_id=route.id,
        business_entity_id=business_entity.id,
        enabled_components=["fuel", "toll", "driver", "overhead", "events"],
        rates={
            "fuel_rate": Decimal("1.85"),
            "event_rate": Decimal("50.00")
        }
    )
    
    # Act
    breakdown = cost_service.calculate_costs(
        route=route,
        transport=transport,
        business=business_entity
    )
    
    # Assert
    assert breakdown is not None
    assert breakdown.route_id == route.id
    
    # Check fuel costs
    assert len(breakdown.fuel_costs) == 2
    assert "DE" in breakdown.fuel_costs
    assert "PL" in breakdown.fuel_costs
    assert breakdown.fuel_costs["DE"] > 0
    assert breakdown.fuel_costs["PL"] > 0
    
    # Check toll costs
    assert len(breakdown.toll_costs) == 2
    assert "DE" in breakdown.toll_costs
    assert "PL" in breakdown.toll_costs
    assert breakdown.toll_costs["DE"] > 0
    assert breakdown.toll_costs["PL"] > 0
    
    # Check driver costs (2 days)
    assert breakdown.driver_costs == Decimal("500.00")  # 2 days * 250.00
    
    # Check overhead costs
    assert breakdown.overhead_costs == Decimal("250.00")  # 100.00 + 150.00
    
    # Check event costs
    assert len(breakdown.timeline_event_costs) == 3
    assert "pickup" in breakdown.timeline_event_costs
    assert "rest" in breakdown.timeline_event_costs
    assert "delivery" in breakdown.timeline_event_costs
    assert all(cost == Decimal("50.00") for cost in breakdown.timeline_event_costs.values())
    
    # Check total cost
    assert breakdown.total_cost > 0
    assert breakdown.total_cost == (
        sum(breakdown.fuel_costs.values()) +
        sum(breakdown.toll_costs.values()) +
        breakdown.driver_costs +
        breakdown.overhead_costs +
        sum(breakdown.timeline_event_costs.values())
    )


def test_calculate_costs_no_components(
    cost_service,
    route,
    transport,
    business_entity
):
    """Test cost calculation with no components enabled."""
    # Arrange
    settings = cost_service.create_cost_settings(
        route_id=route.id,
        business_entity_id=business_entity.id,
        enabled_components=["fuel"],  # Need at least one component
        rates={}
    )
    
    # Act
    breakdown = cost_service.calculate_costs(
        route=route,
        transport=transport,
        business=business_entity
    )
    
    # Assert
    assert breakdown is not None
    assert breakdown.route_id == route.id
    assert all(cost == Decimal("0") for cost in breakdown.toll_costs.values())
    assert breakdown.driver_costs == Decimal("0")
    assert breakdown.overhead_costs == Decimal("0")
    assert all(cost == Decimal("0") for cost in breakdown.timeline_event_costs.values())
    # Fuel costs will be non-zero since it's enabled
    assert any(cost > 0 for cost in breakdown.fuel_costs.values())


def test_calculate_costs_missing_settings(
    cost_service,
    route,
    transport,
    business_entity
):
    """Test cost calculation with missing settings."""
    # Act & Assert
    with pytest.raises(ValueError, match="Cost settings not found for route"):
        cost_service.calculate_costs(
            route=route,
            transport=transport,
            business=business_entity
        )


def test_calculate_costs_partial_components(
    cost_service,
    route,
    transport,
    business_entity
):
    """Test cost calculation with only some components enabled."""
    # Arrange
    settings = cost_service.create_cost_settings(
        route_id=route.id,
        business_entity_id=business_entity.id,
        enabled_components=["fuel", "driver"],  # Only fuel and driver costs
        rates={
            "fuel_rate": Decimal("1.85")
        }
    )
    
    # Act
    breakdown = cost_service.calculate_costs(
        route=route,
        transport=transport,
        business=business_entity
    )
    
    # Assert
    assert breakdown is not None
    assert breakdown.route_id == route.id
    
    # Fuel costs should be present
    assert all(cost > 0 for cost in breakdown.fuel_costs.values())
    
    # Driver costs should be present
    assert breakdown.driver_costs > 0
    
    # Other costs should be zero
    assert all(cost == Decimal("0") for cost in breakdown.toll_costs.values())
    assert breakdown.overhead_costs == Decimal("0")
    assert all(cost == Decimal("0") for cost in breakdown.timeline_event_costs.values())
    
    # Total should be sum of fuel and driver costs only
    assert breakdown.total_cost == (
        sum(breakdown.fuel_costs.values()) +
        breakdown.driver_costs
    ) 