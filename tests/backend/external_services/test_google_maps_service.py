"""Unit tests for Google Maps service."""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from backend.domain.entities.route import Location, RouteSegment
from backend.infrastructure.external_services.google_maps_service import (
    GoogleMapsService,
    GoogleMapsServiceError,
    DEFAULT_MODE,
    DEFAULT_UNITS,
    DEFAULT_LANGUAGE
)


@pytest.fixture
def mock_googlemaps():
    """Create a mock Google Maps client."""
    with patch("backend.infrastructure.external_services.google_maps_service.googlemaps.Client") as mock:
        mock_instance = Mock()
        mock_instance.directions = Mock()
        mock_instance.distance_matrix = Mock()
        mock_instance.geocode = Mock()
        mock_instance.reverse_geocode = Mock()
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def google_maps_service(test_config, mock_googlemaps):
    """Create a Google Maps service instance with test configuration."""
    return GoogleMapsService(
        api_key=test_config.GOOGLE_MAPS.API_KEY,
        timeout=test_config.GOOGLE_MAPS.TIMEOUT,
        max_retries=test_config.GOOGLE_MAPS.MAX_RETRIES,
        retry_delay=test_config.GOOGLE_MAPS.RETRY_DELAY
    )


@pytest.fixture
def sample_locations():
    """Create sample origin and destination locations."""
    origin = Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )
    destination = Location(
        id=uuid4(),
        latitude=48.8566,
        longitude=2.3522,
        address="Paris, France"
    )
    return origin, destination


def test_initialization(test_config, mock_googlemaps):
    """Test service initialization."""
    service = GoogleMapsService(
        api_key=test_config.GOOGLE_MAPS.API_KEY,
        timeout=test_config.GOOGLE_MAPS.TIMEOUT,
        max_retries=test_config.GOOGLE_MAPS.MAX_RETRIES,
        retry_delay=test_config.GOOGLE_MAPS.RETRY_DELAY
    )
    assert service.api_key == test_config.GOOGLE_MAPS.API_KEY
    assert service.mode == DEFAULT_MODE
    assert service.units == DEFAULT_UNITS
    assert service.language == DEFAULT_LANGUAGE


def test_initialization_without_api_key():
    """Test service initialization without API key."""
    with pytest.raises(ValueError, match="API key is required"):
        GoogleMapsService(api_key=None)


def test_calculate_route_success(google_maps_service, sample_locations):
    """Test successful route calculation."""
    origin, destination = sample_locations

    # Mock response in the format our service expects
    mock_response = [{
        "legs": [{
            "distance": {"value": 1000000},  # 1000 km in meters
            "duration": {"value": 36000},    # 10 hours in seconds
            "steps": [{
                "distance": {"value": 1000000},
                "duration": {"value": 36000},
                "start_location": {"lat": 52.5200, "lng": 13.4050},
                "end_location": {"lat": 48.8566, "lng": 2.3522}
            }]
        }]
    }]
    google_maps_service.client.directions.return_value = mock_response

    # Call calculate_route and unpack the returned tuple
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination)
    
    # Verify the returned values
    assert distance_km == 1000.0
    assert duration_hours == 10.0
    assert len(segments) == 1
    assert segments[0].start_location_id == origin.id
    assert segments[0].end_location_id == destination.id

    # Verify the API was called with correct parameters
    google_maps_service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE
    )


def test_calculate_route_retry_success(google_maps_service, sample_locations):
    """Test successful route calculation after temporary failure."""
    origin, destination = sample_locations

    # Mock response that fails first, then succeeds
    mock_response = [{
        "legs": [{
            "distance": {"value": 1000000},
            "duration": {"value": 36000},
            "steps": [{
                "distance": {"value": 1000000},
                "duration": {"value": 36000},
                "start_location": {"lat": 52.5200, "lng": 13.4050},
                "end_location": {"lat": 48.8566, "lng": 2.3522}
            }]
        }]
    }]
    
    # Set up the mock to fail first then succeed
    google_maps_service.client.directions.side_effect = [
        Exception("Temporary error"),
        mock_response
    ]

    # Call calculate_route and unpack the returned tuple
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination)
    
    # Verify the returned values
    assert distance_km == 1000.0
    assert duration_hours == 10.0
    assert len(segments) == 1

    # Verify the API was called with correct parameters
    assert google_maps_service.client.directions.call_count == 2
    google_maps_service.client.directions.assert_called_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE
    )


def test_calculate_route_with_departure_time(google_maps_service, sample_locations):
    """Test route calculation with departure time."""
    origin, destination = sample_locations
    departure_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Mock response
    mock_response = [{
        "legs": [{
            "distance": {"value": 1000000},
            "duration": {"value": 36000},
            "steps": [{
                "distance": {"value": 1000000},
                "duration": {"value": 36000},
                "start_location": {"lat": 52.5200, "lng": 13.4050},
                "end_location": {"lat": 48.8566, "lng": 2.3522}
            }]
        }]
    }]
    google_maps_service.client.directions.return_value = mock_response

    route = google_maps_service.calculate_route(origin, destination, departure_time=departure_time)
    distance_km, duration_hours, segments = route
    assert distance_km == 1000.0
    assert duration_hours == 10.0
    assert len(segments) == 1

    # Verify the API was called with correct parameters
    google_maps_service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE,
        departure_time=departure_time
    )


def test_calculate_route_no_routes_found(google_maps_service, sample_locations):
    """Test handling when no routes are found."""
    origin, destination = sample_locations
    google_maps_service.client.directions.return_value = []

    with pytest.raises(GoogleMapsServiceError, match="No route found"):
        google_maps_service.calculate_route(origin, destination)


def test_calculate_route_api_error(google_maps_service, sample_locations):
    """Test handling of API errors."""
    origin, destination = sample_locations
    google_maps_service.client.directions.side_effect = Exception("API Error")

    with pytest.raises(GoogleMapsServiceError, match="Failed to calculate route: API Error"):
        google_maps_service.calculate_route(origin, destination)


def test_calculate_route_invalid_locations(google_maps_service):
    """Test handling of invalid locations."""
    valid_location = Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )
    
    # Test invalid origin
    with pytest.raises(ValidationError) as exc_info:
        google_maps_service.calculate_route(
            Location(
                id=uuid4(),
                latitude=None,
                longitude=None,
                address=""
            ),
            valid_location
        )
    assert "Input should be a valid number" in str(exc_info.value)

    # Test invalid destination
    with pytest.raises(ValidationError) as exc_info:
        google_maps_service.calculate_route(
            valid_location,
            Location(
                id=uuid4(),
                latitude=None,
                longitude=None,
                address=""
            )
        )
    assert "Input should be a valid number" in str(exc_info.value)


def test_calculate_route_invalid_avoid_options(google_maps_service, sample_locations):
    """Test handling of invalid avoid options."""
    origin, destination = sample_locations
    invalid_avoid = ["invalid_option"]

    with pytest.raises(ValueError, match="Invalid avoid options: invalid_option"):
        google_maps_service.calculate_route(origin, destination, avoid=invalid_avoid) 