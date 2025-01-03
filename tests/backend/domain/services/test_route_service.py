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
    EmptyDriving,
    RouteStatus,
    EventStatus
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
        """Save empty driving instance."""
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
        """Calculate route between two locations."""
        route_id = uuid4()  # This will be updated by the route service
        return (
            500.0,  # distance in km
            8.0,    # duration in hours
            [
                CountrySegment(
                    id=uuid4(),
                    route_id=route_id,
                    country_code="PL",
                    distance_km=250.0,
                    duration_hours=4.0,
                    start_location_id=origin.id,
                    end_location_id=destination.id,
                    segment_order=0
                ),
                CountrySegment(
                    id=uuid4(),
                    route_id=route_id,
                    country_code="DE",
                    distance_km=250.0,
                    duration_hours=4.0,
                    start_location_id=origin.id,
                    end_location_id=destination.id,
                    segment_order=1
                )
            ]
        )


@pytest.fixture
def origin() -> Location:
    """Create a test origin location."""
    return Location(
        id=uuid4(),
        latitude=52.237049,
        longitude=21.017532,
        address="Warsaw, Poland"
    )


@pytest.fixture
def destination() -> Location:
    """Create a test destination location."""
    return Location(
        id=uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin, Germany"
    )


@pytest.fixture
def pickup_time() -> datetime:
    """Create a test pickup time."""
    return datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture
def delivery_time(pickup_time) -> datetime:
    """Create a test delivery time."""
    return pickup_time + timedelta(days=1)


@pytest.fixture
def route_repo() -> MockRouteRepository:
    """Create a mock route repository."""
    return MockRouteRepository()


@pytest.fixture
def location_repo() -> MockLocationRepository:
    """Create a mock location repository."""
    return MockLocationRepository()


@pytest.fixture
def route_calculator() -> MockRouteCalculator:
    """Create a mock route calculator."""
    return MockRouteCalculator()


@pytest.fixture
def route_service(route_repo, location_repo, route_calculator) -> RouteService:
    """Create a route service instance."""
    return RouteService(
        route_repo=route_repo,
        location_repo=location_repo,
        route_calculator=route_calculator
    )


@pytest.fixture
def sample_route(route_service, origin, destination, pickup_time, delivery_time) -> Route:
    """Create a sample route for testing."""
    empty_driving = EmptyDriving(
        id=uuid4(),
        distance_km=200.0,
        duration_hours=4.0
    )

    route = Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        empty_driving_id=empty_driving.id,
        total_distance_km=700.0,
        total_duration_hours=9.0,
        is_feasible=True,
        status=RouteStatus.DRAFT
    )

    # Add timeline events
    events = [
        TimelineEvent(
            id=uuid4(),
            route_id=route.id,
            type="pickup",
            location_id=origin.id,
            planned_time=pickup_time,
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEvent(
            id=uuid4(),
            route_id=route.id,
            type="rest",
            location_id=destination.id,
            planned_time=pickup_time + timedelta(hours=12),
            duration_hours=1.0,
            event_order=2
        ),
        TimelineEvent(
            id=uuid4(),
            route_id=route.id,
            type="delivery",
            location_id=destination.id,
            planned_time=delivery_time,
            duration_hours=1.0,
            event_order=3
        )
    ]

    # Add country segments
    segments = [
        CountrySegment(
            id=uuid4(),
            route_id=route.id,
            country_code="DE",
            distance_km=200.0,  # Empty driving
            duration_hours=4.0,
            start_location_id=origin.id,
            end_location_id=origin.id,
            segment_order=0
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route.id,
            country_code="DE",
            distance_km=550.0,
            duration_hours=5.5,
            start_location_id=origin.id,
            end_location_id=destination.id,
            segment_order=1
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route.id,
            country_code="FR",
            distance_km=500.0,
            duration_hours=4.5,
            start_location_id=destination.id,
            end_location_id=destination.id,
            segment_order=2
        )
    ]

    route.timeline_events = events
    route.country_segments = segments

    return route_service._route_repo.save(route)


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
    
    # Create intermediate locations
    intermediate_location1 = Location(
        id=uuid4(),
        latitude=51.0,
        longitude=10.0,
        address="Intermediate Point 1"
    )
    
    intermediate_location2 = Location(
        id=uuid4(),
        latitude=49.0,
        longitude=8.0,
        address="Intermediate Point 2"
    )
    
    segments = [
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="DE",
            distance_km=300.0,
            duration_hours=4.5,
            start_location_id=origin.id,
            end_location_id=intermediate_location1.id,
            segment_order=0
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="DE",
            distance_km=200.0,
            duration_hours=3.0,
            start_location_id=intermediate_location1.id,
            end_location_id=intermediate_location2.id,
            segment_order=1
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="FR",
            distance_km=250.0,
            duration_hours=3.5,
            start_location_id=intermediate_location2.id,
            end_location_id=destination.id,
            segment_order=2
        )
    ]
    
    # Save intermediate locations to repository
    route_service._location_repo.save(intermediate_location1)
    route_service._location_repo.save(intermediate_location2)
    
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
    
    # Check rest event - should use first segment's end location
    rest = events[1]
    assert rest.type == "rest"
    assert rest.location_id == intermediate_location1.id  # First segment's end location
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


def test_handle_cargo_status_change_to_in_transit(route_service, sample_route):
    """Test handling cargo status change to in_transit."""
    # Arrange
    route_service._route_repo.save(sample_route)
    
    # Act
    route_service.handle_cargo_status_change(sample_route.cargo_id, "in_transit")
    
    # Assert
    updated_route = route_service._route_repo.find_by_id(sample_route.id)
    assert updated_route.status == RouteStatus.IN_PROGRESS
    
    # Check timeline events
    pickup_event = next(event for event in updated_route.timeline_events if event.type == "pickup")
    assert pickup_event.status == EventStatus.IN_PROGRESS
    assert pickup_event.actual_time is not None
    
    rest_event = next(event for event in updated_route.timeline_events if event.type == "rest")
    assert rest_event.status == EventStatus.PENDING
    assert rest_event.actual_time is None
    
    delivery_event = next(event for event in updated_route.timeline_events if event.type == "delivery")
    assert delivery_event.status == EventStatus.PENDING
    assert delivery_event.actual_time is None


def test_handle_cargo_status_change_to_delivered(route_service, sample_route):
    """Test handling cargo status change to delivered."""
    # Arrange
    route_service._route_repo.save(sample_route)
    
    # Act
    route_service.handle_cargo_status_change(sample_route.cargo_id, "delivered")
    
    # Assert
    updated_route = route_service._route_repo.find_by_id(sample_route.id)
    assert updated_route.status == RouteStatus.COMPLETED
    
    # Check all events are completed
    for event in updated_route.timeline_events:
        assert event.status == EventStatus.COMPLETED
        assert event.actual_time is not None


def test_handle_cargo_status_change_to_cancelled(route_service, sample_route):
    """Test handling cargo status change to cancelled."""
    # Arrange
    route_service._route_repo.save(sample_route)
    
    # First set some events as completed
    sample_route.timeline_events[0].status = EventStatus.COMPLETED
    sample_route.timeline_events[0].actual_time = datetime.now(timezone.utc)
    route_service._route_repo.save(sample_route)
    
    # Act
    route_service.handle_cargo_status_change(sample_route.cargo_id, "cancelled")
    
    # Assert
    updated_route = route_service._route_repo.find_by_id(sample_route.id)
    assert updated_route.status == RouteStatus.CANCELLED
    
    # Check completed events remain completed
    assert updated_route.timeline_events[0].status == EventStatus.COMPLETED
    
    # Check other events are cancelled
    for event in updated_route.timeline_events[1:]:
        assert event.status == EventStatus.CANCELLED 