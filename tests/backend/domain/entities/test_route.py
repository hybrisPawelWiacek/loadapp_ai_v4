"""Tests for route domain entities."""
import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import ValidationError

from backend.domain.entities.route import (
    Location,
    EmptyDriving,
    TimelineEvent,
    CountrySegment,
    RouteSegment,
    Route
)


@pytest.fixture
def sample_location():
    """Create sample location."""
    return Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


@pytest.fixture
def sample_empty_driving():
    """Create sample empty driving segment."""
    return EmptyDriving(
        id=uuid4(),
        distance_km=200.0,  # Default value
        duration_hours=4.0  # Default value
    )


@pytest.fixture
def sample_timeline_event():
    """Create sample timeline event."""
    return TimelineEvent(
        id=uuid4(),
        route_id=uuid4(),
        type="pickup",
        location_id=uuid4(),
        planned_time=datetime.now(timezone.utc),
        event_order=1
    )


@pytest.fixture
def sample_country_segment():
    """Create sample country segment."""
    return CountrySegment(
        id=uuid4(),
        route_id=uuid4(),
        country_code="DE",
        distance_km=500.0,
        duration_hours=6.0,
        start_location_id=uuid4(),
        end_location_id=uuid4(),
        segment_order=0
    )


@pytest.fixture
def sample_route_segment():
    """Create sample route segment."""
    return RouteSegment(
        distance_km=500.0,
        duration_hours=6.0,
        start_location_id=uuid4(),
        end_location_id=uuid4()
    )


@pytest.fixture
def sample_route(sample_empty_driving, sample_timeline_event, sample_country_segment):
    """Create sample route."""
    return Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin_id=uuid4(),
        destination_id=uuid4(),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=uuid4(),
        total_distance_km=700.0,  # Including empty driving
        total_duration_hours=10.0,  # Including empty driving
        is_feasible=True,
        status="draft"
    )


def test_location_creation(sample_location):
    """Test location creation."""
    assert isinstance(sample_location.id, UUID)
    assert sample_location.latitude == 52.5200
    assert sample_location.longitude == 13.4050
    assert sample_location.address == "Berlin, Germany"


def test_empty_driving_creation(sample_empty_driving):
    """Test empty driving creation."""
    assert sample_empty_driving.distance_km == 200.0  # Default value
    assert sample_empty_driving.duration_hours == 4.0  # Default value


def test_timeline_event_creation(sample_timeline_event):
    """Test timeline event creation."""
    assert isinstance(sample_timeline_event.id, UUID)
    assert isinstance(sample_timeline_event.route_id, UUID)
    assert sample_timeline_event.type == "pickup"
    assert isinstance(sample_timeline_event.location_id, UUID)
    assert isinstance(sample_timeline_event.planned_time, datetime)
    assert sample_timeline_event.event_order == 1
    assert sample_timeline_event.duration_hours == 1.0  # Default value


def test_country_segment_creation(sample_country_segment):
    """Test country segment creation."""
    assert isinstance(sample_country_segment.id, UUID)
    assert isinstance(sample_country_segment.route_id, UUID)
    assert sample_country_segment.country_code == "DE"
    assert sample_country_segment.distance_km == 500.0
    assert sample_country_segment.duration_hours == 6.0
    assert isinstance(sample_country_segment.start_location_id, UUID)
    assert isinstance(sample_country_segment.end_location_id, UUID)


def test_route_segment_creation(sample_route_segment):
    """Test route segment creation."""
    assert sample_route_segment.distance_km == 500.0
    assert sample_route_segment.duration_hours == 6.0
    assert isinstance(sample_route_segment.start_location_id, UUID)
    assert isinstance(sample_route_segment.end_location_id, UUID)


def test_route_creation(sample_route):
    """Test route creation."""
    assert isinstance(sample_route.id, UUID)
    assert isinstance(sample_route.transport_id, UUID)
    assert isinstance(sample_route.business_entity_id, UUID)
    assert isinstance(sample_route.cargo_id, UUID)
    assert isinstance(sample_route.origin_id, UUID)
    assert isinstance(sample_route.destination_id, UUID)
    assert isinstance(sample_route.pickup_time, datetime)
    assert isinstance(sample_route.delivery_time, datetime)
    assert isinstance(sample_route.empty_driving_id, UUID)
    assert sample_route.total_distance_km == 700.0
    assert sample_route.total_duration_hours == 10.0
    assert sample_route.is_feasible is True
    assert sample_route.status == "draft"


def test_location_validation():
    """Test location validation."""
    with pytest.raises(ValidationError):
        Location(
            id="invalid",  # Should be UUID
            latitude="invalid",  # Should be float
            longitude="invalid",  # Should be float
            address=123  # Should be string
        )


def test_country_segment_validation():
    """Test country segment validation."""
    with pytest.raises(ValidationError):
        CountrySegment(
            id="invalid",  # Should be UUID
            route_id="invalid",  # Should be UUID
            country_code=123,  # Should be string
            distance_km="invalid",  # Should be float
            duration_hours="invalid",  # Should be float
            start_location_id="invalid",  # Should be UUID
            end_location_id="invalid"  # Should be UUID
        )


def test_route_validation():
    """Test route validation."""
    with pytest.raises((TypeError, ValueError)):  # Can raise either depending on validation
        Route(
            id="invalid",  # Should be UUID
            transport_id="invalid",  # Should be UUID
            business_entity_id="invalid",  # Should be UUID
            cargo_id="invalid",  # Should be UUID
            origin_id="invalid",  # Should be UUID
            destination_id="invalid",  # Should be UUID
            pickup_time="invalid",  # Should be datetime
            delivery_time="invalid",  # Should be datetime
            empty_driving_id="invalid",  # Should be UUID
            total_distance_km="invalid",  # Should be float
            total_duration_hours="invalid",  # Should be float
            is_feasible="invalid",  # Should be bool
            status="invalid"  # Should be RouteStatus
        ) 