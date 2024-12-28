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
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


@pytest.fixture
def sample_empty_driving():
    """Create sample empty driving segment."""
    return EmptyDriving()  # Uses default values


@pytest.fixture
def sample_timeline_event(sample_location):
    """Create sample timeline event."""
    return TimelineEvent(
        id=uuid4(),
        type="pickup",
        location=sample_location,
        planned_time=datetime.now(timezone.utc),
        event_order=1
    )


@pytest.fixture
def sample_country_segment(sample_location):
    """Create sample country segment."""
    return CountrySegment(
        country_code="DE",
        distance_km=500.0,
        duration_hours=6.0,
        start_location=sample_location,
        end_location=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        )
    )


@pytest.fixture
def sample_route_segment(sample_location):
    """Create sample route segment."""
    return RouteSegment(
        distance_km=500.0,
        duration_hours=6.0,
        start_location=sample_location,
        end_location=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        )
    )


@pytest.fixture
def sample_route(sample_location, sample_empty_driving, sample_timeline_event, sample_country_segment):
    """Create sample route."""
    return Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin=sample_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving=sample_empty_driving,
        timeline_events=[sample_timeline_event],
        country_segments=[sample_country_segment],
        total_distance_km=700.0,  # Including empty driving
        total_duration_hours=10.0  # Including empty driving
    )


def test_location_creation(sample_location):
    """Test location creation."""
    assert sample_location.latitude == 52.5200
    assert sample_location.longitude == 13.4050
    assert sample_location.address == "Berlin, Germany"


def test_empty_driving_creation(sample_empty_driving):
    """Test empty driving creation."""
    assert sample_empty_driving.distance_km == 200.0  # Default value
    assert sample_empty_driving.duration_hours == 4.0  # Default value


def test_timeline_event_creation(sample_timeline_event, sample_location):
    """Test timeline event creation."""
    assert isinstance(sample_timeline_event.id, UUID)
    assert sample_timeline_event.type == "pickup"
    assert sample_timeline_event.location == sample_location
    assert isinstance(sample_timeline_event.planned_time, datetime)
    assert sample_timeline_event.event_order == 1
    assert sample_timeline_event.duration_hours == 1.0  # Default value


def test_country_segment_creation(sample_country_segment, sample_location):
    """Test country segment creation."""
    assert sample_country_segment.country_code == "DE"
    assert sample_country_segment.distance_km == 500.0
    assert sample_country_segment.duration_hours == 6.0
    assert sample_country_segment.start_location == sample_location
    assert sample_country_segment.end_location.address == "Paris, France"


def test_route_segment_creation(sample_route_segment, sample_location):
    """Test route segment creation."""
    assert sample_route_segment.distance_km == 500.0
    assert sample_route_segment.duration_hours == 6.0
    assert sample_route_segment.start_location == sample_location
    assert sample_route_segment.end_location.address == "Paris, France"


def test_route_creation(sample_route, sample_location, sample_empty_driving):
    """Test route creation."""
    assert isinstance(sample_route.id, UUID)
    assert isinstance(sample_route.transport_id, UUID)
    assert isinstance(sample_route.business_entity_id, UUID)
    assert isinstance(sample_route.cargo_id, UUID)
    assert sample_route.origin == sample_location
    assert sample_route.destination.address == "Paris, France"
    assert isinstance(sample_route.pickup_time, datetime)
    assert isinstance(sample_route.delivery_time, datetime)
    assert sample_route.empty_driving == sample_empty_driving
    assert len(sample_route.timeline_events) == 1
    assert len(sample_route.country_segments) == 1
    assert sample_route.total_distance_km == 700.0
    assert sample_route.total_duration_hours == 10.0
    assert sample_route.is_feasible is True


def test_location_validation():
    """Test location validation."""
    with pytest.raises(ValidationError):
        Location(
            latitude="invalid",  # Should be float
            longitude="invalid",  # Should be float
            address=123  # Should be string
        )


def test_country_segment_validation():
    """Test country segment validation."""
    with pytest.raises(ValidationError):
        CountrySegment(
            country_code=123,  # Should be string
            distance_km="invalid",  # Should be float
            duration_hours="invalid",  # Should be float
            start_location="invalid",  # Should be Location
            end_location="invalid"  # Should be Location
        )


def test_route_validation(sample_location, sample_empty_driving):
    """Test route validation."""
    with pytest.raises((TypeError, ValueError)):  # Can raise either depending on validation
        Route(
            id="invalid",  # Should be UUID
            transport_id="invalid",  # Should be UUID
            business_entity_id="invalid",  # Should be UUID
            cargo_id="invalid",  # Should be UUID
            origin="invalid",  # Should be Location
            destination="invalid",  # Should be Location
            pickup_time="invalid",  # Should be datetime
            delivery_time="invalid",  # Should be datetime
            empty_driving="invalid",  # Should be EmptyDriving
            timeline_events="invalid",  # Should be list
            country_segments="invalid",  # Should be list
            total_distance_km="invalid",  # Should be float
            total_duration_hours="invalid"  # Should be float
        ) 