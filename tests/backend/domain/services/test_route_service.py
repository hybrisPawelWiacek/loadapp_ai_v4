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
        self.empty_drivings = {}
        
    def save(self, route: Route) -> Route:
        """Save a route instance."""
        self.routes[route.id] = route
        return route
        
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        return self.routes.get(id)

    def find_by_cargo_id(self, cargo_id: UUID) -> List[Route]:
        """Find routes by cargo ID."""
        return [route for route in self.routes.values() if route.cargo_id == cargo_id]

    def save_empty_driving(self, empty_driving: EmptyDriving) -> EmptyDriving:
        """Save an empty driving instance."""
        self.empty_drivings[empty_driving.id] = empty_driving
        return empty_driving


class MockLocationRepository:
    """Mock repository for Location entity."""
    
    def __init__(self):
        self.locations = {}
        
    def save(self, location: Location) -> Location:
        """Save a location instance."""
        self.locations[location.id] = location
        return location
        
    def find_by_id(self, id: UUID) -> Optional[Location]:
        """Find a location by ID."""
        return self.locations.get(id)


class MockRouteCalculator:
    """Mock route calculator."""
    
    def calculate_route(
        self,
        origin: Location,
        destination: Location
    ) -> tuple[float, float, List[CountrySegment]]:
        """Calculate route details and country segments."""
        # Return mock data with reasonable values
        distance = 500.0  # 500 km
        duration = 8.0    # 8 hours
        
        intermediate_location = Location(
            id=uuid4(),
            latitude=51.0,
            longitude=10.0,
            address="Intermediate Point"
        )
        
        # Create a temporary route_id that will be overwritten by route service
        temp_route_id = uuid4()
        
        segments = [
            CountrySegment(
                id=uuid4(),
                route_id=temp_route_id,  # Will be overwritten by route service
                country_code="DE",
                distance_km=300.0,
                duration_hours=4.5,
                start_location_id=origin.id,
                end_location_id=intermediate_location.id
            ),
            CountrySegment(
                id=uuid4(),
                route_id=temp_route_id,  # Will be overwritten by route service
                country_code="PL",
                distance_km=200.0,
                duration_hours=3.5,
                start_location_id=intermediate_location.id,
                end_location_id=destination.id
            )
        ]
        
        return distance, duration, segments


@pytest.fixture
def origin() -> Location:
    """Create sample origin location."""
    return Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


@pytest.fixture
def destination() -> Location:
    """Create sample destination location."""
    return Location(
        id=uuid4(),
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
def location_repo() -> MockLocationRepository:
    """Create mock location repository."""
    return MockLocationRepository()


@pytest.fixture
def route_calculator() -> MockRouteCalculator:
    """Create mock route calculator."""
    return MockRouteCalculator()


@pytest.fixture
def route_service(route_repo, location_repo, route_calculator) -> RouteService:
    """Create route service with mock dependencies."""
    return RouteService(
        route_repo=route_repo,
        location_repo=location_repo,
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
    
    # Save locations to repository
    route_service._location_repo.save(origin)
    route_service._location_repo.save(destination)
    
    # Act
    route = route_service.create_route(
        transport_id=transport_id,
        business_entity_id=business_entity_id,
        cargo_id=cargo_id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Assert
    assert route is not None
    assert isinstance(route.id, UUID)
    assert route.transport_id == transport_id
    assert route.business_entity_id == business_entity_id
    assert route.cargo_id == cargo_id
    assert route.origin_id == origin.id
    assert route.destination_id == destination.id
    assert route.pickup_time == pickup_time
    assert route.delivery_time == delivery_time
    assert isinstance(route.empty_driving_id, UUID)
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
    # Create a route_id for testing
    route_id = uuid4()
    
    # Create a mock segment
    intermediate_location = Location(
        id=uuid4(),
        latitude=51.0,
        longitude=10.0,
        address="Intermediate Point"
    )
    
    segments = [
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="DE",
            distance_km=300.0,
            duration_hours=4.5,
            start_location_id=origin.id,
            end_location_id=intermediate_location.id
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="PL",
            distance_km=200.0,
            duration_hours=3.5,
            start_location_id=intermediate_location.id,
            end_location_id=destination.id
        )
    ]
    
    # Act
    events = route_service._generate_timeline_events(
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        route_id=route_id,
        segments=segments
    )
    
    # Assert
    assert len(events) == 3
    
    # Check pickup event
    pickup = events[0]
    assert pickup.type == "pickup"
    assert pickup.location_id == origin.id
    assert pickup.route_id == route_id
    assert pickup.planned_time == pickup_time
    assert pickup.duration_hours == 1.0
    assert pickup.event_order == 1
    
    # Check rest event
    rest = events[1]
    assert rest.type == "rest"
    assert rest.location_id == intermediate_location.id  # Should use first segment's end location
    assert rest.route_id == route_id
    assert rest.duration_hours == 1.0
    assert rest.event_order == 2
    
    # Check delivery event
    delivery = events[2]
    assert delivery.type == "delivery"
    assert delivery.location_id == destination.id
    assert delivery.route_id == route_id
    assert delivery.planned_time == delivery_time
    assert delivery.duration_hours == 1.0
    assert delivery.event_order == 3


def test_timeline_events_generation_no_segments(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test timeline events generation when no segments are provided."""
    # Create a route_id for testing
    route_id = uuid4()
    
    # Act
    events = route_service._generate_timeline_events(
        origin=origin,
        destination=destination,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        route_id=route_id,
        segments=None
    )
    
    # Assert
    assert len(events) == 3
    
    # Check pickup event
    pickup = events[0]
    assert pickup.type == "pickup"
    assert pickup.location_id == origin.id
    
    # Check rest event - should default to origin location
    rest = events[1]
    assert rest.type == "rest"
    assert rest.location_id == origin.id
    
    # Check delivery event
    delivery = events[2]
    assert delivery.type == "delivery"
    assert delivery.location_id == destination.id


def test_get_route_success(
    route_service,
    origin,
    destination,
    pickup_time,
    delivery_time
):
    """Test successful route retrieval."""
    # Arrange
    transport_id = uuid4()
    business_entity_id = uuid4()
    cargo_id = uuid4()
    
    # Save locations to repository
    route_service._location_repo.save(origin)
    route_service._location_repo.save(destination)
    
    # Create a route
    created_route = route_service.create_route(
        transport_id=transport_id,
        business_entity_id=business_entity_id,
        cargo_id=cargo_id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Act
    retrieved_route = route_service.get_route(created_route.id)
    
    # Assert
    assert retrieved_route is not None
    assert retrieved_route.id == created_route.id
    assert retrieved_route.transport_id == transport_id
    assert retrieved_route.business_entity_id == business_entity_id
    assert retrieved_route.cargo_id == cargo_id
    assert retrieved_route.origin_id == origin.id
    assert retrieved_route.destination_id == destination.id
    assert retrieved_route.pickup_time == pickup_time
    assert retrieved_route.delivery_time == delivery_time


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
    """Test route feasibility validation."""
    # Arrange
    transport_id = uuid4()
    business_entity_id = uuid4()
    cargo_id = uuid4()
    
    # Save locations to repository
    route_service._location_repo.save(origin)
    route_service._location_repo.save(destination)
    
    # Create a route
    route = route_service.create_route(
        transport_id=transport_id,
        business_entity_id=business_entity_id,
        cargo_id=cargo_id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=pickup_time,
        delivery_time=delivery_time
    )
    
    # Act
    is_feasible = route_service.validate_route_feasibility(route)
    
    # Assert
    assert is_feasible is True  # Always true for PoC 