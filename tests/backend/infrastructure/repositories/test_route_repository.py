"""Tests for route repository implementations."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from backend.domain.entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving
)
from backend.infrastructure.repositories.route_repository import SQLRouteRepository


@pytest.fixture
def berlin_location() -> Location:
    """Create a sample location in Berlin."""
    return Location(
        latitude=52.520008,
        longitude=13.404954,
        address="Sample Address, Berlin, Germany"
    )


@pytest.fixture
def warsaw_location() -> Location:
    """Create a sample location in Warsaw."""
    return Location(
        latitude=52.237049,
        longitude=21.017532,
        address="Sample Address, Warsaw, Poland"
    )


@pytest.fixture
def empty_driving() -> EmptyDriving:
    """Create a sample empty driving segment."""
    return EmptyDriving(
        distance_km=200.0,  # Fixed for PoC
        duration_hours=4.0   # Fixed for PoC
    )


@pytest.fixture
def timeline_events(berlin_location: Location) -> list[TimelineEvent]:
    """Create sample timeline events."""
    base_time = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)
    return [
        TimelineEvent(
            id=uuid4(),
            type="pickup",
            location=berlin_location,
            planned_time=base_time,
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEvent(
            id=uuid4(),
            type="rest",
            location=berlin_location,
            planned_time=base_time.replace(hour=12),
            duration_hours=1.0,
            event_order=2
        ),
        TimelineEvent(
            id=uuid4(),
            type="delivery",
            location=berlin_location,
            planned_time=base_time.replace(hour=16),
            duration_hours=1.0,
            event_order=3
        )
    ]


@pytest.fixture
def country_segments(berlin_location: Location, warsaw_location: Location) -> list[CountrySegment]:
    """Create sample country segments."""
    return [
        CountrySegment(
            country_code="DE",
            distance_km=300.0,
            duration_hours=4.0,
            start_location=berlin_location,
            end_location=warsaw_location
        ),
        CountrySegment(
            country_code="PL",
            distance_km=200.0,
            duration_hours=3.0,
            start_location=warsaw_location,
            end_location=warsaw_location
        )
    ]


@pytest.fixture
def route(
    berlin_location: Location,
    warsaw_location: Location,
    empty_driving: EmptyDriving,
    timeline_events: list[TimelineEvent],
    country_segments: list[CountrySegment]
) -> Route:
    """Create a sample route."""
    return Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin=berlin_location,
        destination=warsaw_location,
        pickup_time=timeline_events[0].planned_time,
        delivery_time=timeline_events[-1].planned_time,
        empty_driving=empty_driving,
        timeline_events=timeline_events,
        country_segments=country_segments,
        total_distance_km=500.0,  # Sum of country segments
        total_duration_hours=7.0,  # Sum of country segments
        is_feasible=True
    )


class TestSQLRouteRepository:
    """Test cases for SQLRouteRepository."""

    def test_save_route(self, db: Session, route: Route):
        """Test saving a route instance."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        saved_route = repo.save(route)

        # Assert
        assert isinstance(saved_route, Route)
        assert saved_route.id == route.id
        assert saved_route.transport_id == route.transport_id
        assert saved_route.business_entity_id == route.business_entity_id
        assert saved_route.cargo_id == route.cargo_id
        assert saved_route.is_feasible == route.is_feasible

        # Check locations
        assert saved_route.origin.latitude == route.origin.latitude
        assert saved_route.origin.longitude == route.origin.longitude
        assert saved_route.origin.address == route.origin.address
        assert saved_route.destination.latitude == route.destination.latitude
        assert saved_route.destination.longitude == route.destination.longitude
        assert saved_route.destination.address == route.destination.address

        # Check empty driving
        assert saved_route.empty_driving.distance_km == route.empty_driving.distance_km
        assert saved_route.empty_driving.duration_hours == route.empty_driving.duration_hours

        # Check timeline events
        assert len(saved_route.timeline_events) == len(route.timeline_events)
        for saved_event, original_event in zip(saved_route.timeline_events, route.timeline_events):
            assert saved_event.type == original_event.type
            assert saved_event.location.latitude == original_event.location.latitude
            assert saved_event.location.longitude == original_event.location.longitude
            assert saved_event.location.address == original_event.location.address
            assert saved_event.planned_time == original_event.planned_time
            assert saved_event.duration_hours == original_event.duration_hours
            assert saved_event.event_order == original_event.event_order

        # Check country segments
        assert len(saved_route.country_segments) == len(route.country_segments)
        for saved_segment, original_segment in zip(saved_route.country_segments, route.country_segments):
            assert saved_segment.country_code == original_segment.country_code
            assert saved_segment.distance_km == original_segment.distance_km
            assert saved_segment.duration_hours == original_segment.duration_hours
            assert saved_segment.start_location.latitude == original_segment.start_location.latitude
            assert saved_segment.start_location.longitude == original_segment.start_location.longitude
            assert saved_segment.start_location.address == original_segment.start_location.address
            assert saved_segment.end_location.latitude == original_segment.end_location.latitude
            assert saved_segment.end_location.longitude == original_segment.end_location.longitude
            assert saved_segment.end_location.address == original_segment.end_location.address

    def test_find_route_by_id(self, db: Session, route: Route):
        """Test finding a route by ID."""
        # Arrange
        repo = SQLRouteRepository(db)
        saved_route = repo.save(route)

        # Act
        found_route = repo.find_by_id(saved_route.id)

        # Assert
        assert found_route is not None
        assert found_route.id == route.id
        assert found_route.transport_id == route.transport_id
        assert found_route.business_entity_id == route.business_entity_id
        assert found_route.cargo_id == route.cargo_id
        assert found_route.is_feasible == route.is_feasible

    def test_find_nonexistent_route(self, db: Session):
        """Test finding a route that doesn't exist."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        found_route = repo.find_by_id(uuid4())

        # Assert
        assert found_route is None 