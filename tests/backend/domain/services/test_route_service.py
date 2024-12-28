"""Tests for route service."""
import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from backend.domain.services.route_service import RouteService
from backend.domain.entities.route import (
    Route,
    Location,
    TimelineEvent,
    CountrySegment,
    EmptyDriving
)


class MockRouteRepository:
    """Mock repository for Route entity."""
    
    def __init__(self):
        self.routes = {}
        
    def save(self, route: Route) -> Route:
        """Save a route instance."""
        self.routes[route.id] = route
        return route
        
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        return self.routes.get(id)


class MockRouteCalculator:
    """Mock route calculator."""
    
    def calculate_route(
        self,
        origin: Location,
        destination: Location
    ) -> Tuple[float, float, List[CountrySegment]]:
        """Calculate route details and country segments."""
        # Return mock data with reasonable values
        distance = 500.0  # 500 km
        duration = 8.0    # 8 hours
        
        segments = [
            CountrySegment(
                country_code="DE",
                distance_km=300.0,
                duration_hours=4.5,
                start_location=origin,
                end_location=Location(
                    latitude=51.0,
                    longitude=10.0,
                    address="Intermediate Point"
                )
            ),
            CountrySegment(
                country_code="PL",
                distance_km=200.0,
                duration_hours=3.5,
                start_location=Location(
                    latitude=51.0,
                    longitude=10.0,
                    address="Intermediate Point"
                ),
                end_location=destination
            )
        ]
        
        return distance, duration, segments


@pytest.fixture
def origin() -> Location:
    """Create sample origin location."""
    return Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


@pytest.fixture
def destination() -> Location:
    """Create sample destination location."""
    return Location(
        latitude=52.2297,
        longitude=21.0122,
        address="Warsaw, Poland"
    )


@pytest.fixture
def pickup_time() -> datetime:
    """Create sample pickup time."""
    return datetime.now(timezone.utc)


@pytest.fixture
def delivery_time(pickup_time) -> datetime:
    """Create sample delivery time."""
    return pickup_time + timedelta(hours=12)


@pytest.fixture
def route_repo() -> MockRouteRepository:
    """Create mock route repository."""
    return MockRouteRepository()


@pytest.fixture
def route_calculator() -> MockRouteCalculator:
    """Create mock route calculator."""
    return MockRouteCalculator()


@pytest.fixture
def route_service(route_repo, route_calculator) -> RouteService:
    """Create route service with mock dependencies."""
    return RouteService(
        route_repo=route_repo,
        route_calculator=route_calculator
    )


def test_create_route_success(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test successful route creation."""
    # Arrange
    transport_id = uuid4()
    business_entity_id = uuid4()
    cargo_id = uuid4()
    
    # Act
    route = route_service.create_route(
        transport_id=transport_id,
        business_entity_id=business_entity_id,
        cargo_id=cargo_id,
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Assert
    assert route is not None
    assert isinstance(route.id, UUID)
    assert route.transport_id == transport_id
    assert route.business_entity_id == business_entity_id
    assert route.cargo_id == cargo_id
    assert route.origin == origin
    assert route.destination == destination
    assert route.pickup_time == pickup_time
    assert route.delivery_time == delivery_time
    assert isinstance(route.empty_driving, EmptyDriving)
    assert route.empty_driving.distance_km == 200.0
    assert route.empty_driving.duration_hours == 4.0
    assert len(route.timeline_events) == 3
    assert len(route.country_segments) == 2
    assert route.total_distance_km == 700.0  # 500 (main) + 200 (empty)
    assert route.total_duration_hours == 12.0  # 8 (main) + 4 (empty)
    assert route.is_feasible is True


def test_timeline_events_generation(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test timeline events generation."""
    # Act
    events = route_service._generate_timeline_events(
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Assert
    assert len(events) == 3
    
    # Check pickup event
    pickup = events[0]
    assert pickup.type == "pickup"
    assert pickup.location == origin
    assert pickup.planned_time == pickup_time
    assert pickup.duration_hours == 1.0
    assert pickup.event_order == 1
    
    # Check rest event
    rest = events[1]
    assert rest.type == "rest"
    assert rest.location == origin  # Simplified for PoC
    assert rest.duration_hours == 1.0
    assert rest.event_order == 2
    
    # Check delivery event
    delivery = events[2]
    assert delivery.type == "delivery"
    assert delivery.location == destination
    assert delivery.planned_time == delivery_time
    assert delivery.duration_hours == 1.0
    assert delivery.event_order == 3


def test_get_route_success(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test successful route retrieval."""
    # Arrange
    route = route_service.create_route(
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Act
    retrieved = route_service.get_route(route.id)
    
    # Assert
    assert retrieved is not None
    assert retrieved.id == route.id
    assert retrieved.transport_id == route.transport_id
    assert retrieved.origin == route.origin
    assert retrieved.destination == route.destination


def test_get_route_nonexistent(route_service):
    """Test route retrieval with nonexistent ID."""
    # Act
    route = route_service.get_route(uuid4())
    
    # Assert
    assert route is None


def test_validate_route_feasibility(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test route feasibility validation (always returns True in PoC)."""
    # Arrange
    route = route_service.create_route(
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Act
    is_feasible = route_service.validate_route_feasibility(route)
    
    # Assert
    assert is_feasible is True 