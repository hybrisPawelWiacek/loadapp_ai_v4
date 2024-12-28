"""Unit tests for Google Maps service adapter."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
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
        # Create a mock instance that won't raise errors on initialization
        instance = Mock()
        mock.return_value = instance
        yield mock


@pytest.fixture
def service(mock_googlemaps):
    """Create a Google Maps service instance with mocked client."""
    return GoogleMapsService(api_key="test_key")


@pytest.fixture
def sample_locations():
    """Create sample origin and destination locations."""
    origin = Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )
    destination = Location(
        latitude=48.8566,
        longitude=2.3522,
        address="Paris, France"
    )
    return origin, destination


def test_initialization(mock_googlemaps):
    """Test service initialization."""
    service = GoogleMapsService(api_key="test_key")
    assert service.api_key == "test_key"
    assert service.mode == DEFAULT_MODE
    assert service.units == DEFAULT_UNITS
    assert service.language == DEFAULT_LANGUAGE


def test_initialization_with_custom_params(mock_googlemaps):
    """Test service initialization with custom parameters."""
    service = GoogleMapsService(
        api_key="test_key",
        mode="walking",
        units="imperial",
        language="fr"
    )
    assert service.api_key == "test_key"
    assert service.mode == "walking"
    assert service.units == "imperial"
    assert service.language == "fr"


def test_initialization_without_api_key():
    """Test service initialization without API key."""
    with pytest.raises(ValueError, match="API key is required"):
        GoogleMapsService(api_key=None)


def test_calculate_route_success(service, mock_googlemaps, sample_locations):
    """Test successful route calculation."""
    origin, destination = sample_locations

    # Mock response in the format our service expects
    mock_response = {
        "routes": [{
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
    }
    service.client.directions.return_value = mock_response

    route = service.calculate_route(origin, destination)
    assert isinstance(route, RouteSegment)
    assert route.distance_km == 1000.0
    assert route.duration_hours == 10.0
    assert route.start_location == origin
    assert route.end_location == destination

    # Verify the API was called with correct parameters
    service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE
    )


def test_calculate_route_with_departure_time(service, mock_googlemaps, sample_locations):
    """Test route calculation with departure time."""
    origin, destination = sample_locations
    departure_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Mock response
    mock_response = {
        "routes": [{
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
    }
    service.client.directions.return_value = mock_response

    route = service.calculate_route(origin, destination, departure_time=departure_time)
    assert isinstance(route, RouteSegment)

    # Verify departure_time was passed correctly
    service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE,
        departure_time=departure_time
    )


def test_calculate_route_with_avoid_options(service, mock_googlemaps, sample_locations):
    """Test route calculation with avoid options."""
    origin, destination = sample_locations
    avoid = ["tolls", "highways"]

    # Mock response
    mock_response = {
        "routes": [{
            "legs": [{
                "distance": {"value": 1200000},  # Longer route due to avoidance
                "duration": {"value": 43200},
                "steps": [{
                    "distance": {"value": 1200000},
                    "duration": {"value": 43200},
                    "start_location": {"lat": 52.5200, "lng": 13.4050},
                    "end_location": {"lat": 48.8566, "lng": 2.3522}
                }]
            }]
        }]
    }
    service.client.directions.return_value = mock_response

    route = service.calculate_route(origin, destination, avoid=avoid)
    assert isinstance(route, RouteSegment)

    # Verify avoid options were passed correctly
    service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE,
        avoid="|".join(avoid)
    )


def test_calculate_route_no_routes_found(service, mock_googlemaps, sample_locations):
    """Test handling when no routes are found."""
    origin, destination = sample_locations
    service.client.directions.return_value = {"routes": []}

    with pytest.raises(GoogleMapsServiceError, match="No route found"):
        service.calculate_route(origin, destination)


def test_calculate_route_api_error(service, mock_googlemaps, sample_locations):
    """Test handling of API errors."""
    origin, destination = sample_locations
    service.client.directions.side_effect = Exception("API Error")

    with pytest.raises(GoogleMapsServiceError, match="Failed to calculate route: API Error"):
        service.calculate_route(origin, destination)


def test_calculate_route_invalid_locations(service, mock_googlemaps):
    """Test handling of invalid locations."""
    valid_location = Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )
    
    # Test invalid origin
    with pytest.raises(ValidationError) as exc_info:
        service.calculate_route(
            Location(latitude=None, longitude=None, address=""),
            valid_location
        )
    assert "Input should be a valid number" in str(exc_info.value)

    # Test invalid destination
    with pytest.raises(ValidationError) as exc_info:
        service.calculate_route(
            valid_location,
            Location(latitude=None, longitude=None, address="")
        )
    assert "Input should be a valid number" in str(exc_info.value)


def test_calculate_route_invalid_avoid_options(service, mock_googlemaps, sample_locations):
    """Test handling of invalid avoid options."""
    origin, destination = sample_locations
    invalid_avoid = ["invalid_option"]

    with pytest.raises(ValueError, match="Invalid avoid options: invalid_option"):
        service.calculate_route(origin, destination, avoid=invalid_avoid)


def test_calculate_route_with_waypoints(service, mock_googlemaps, sample_locations):
    """Test route calculation with waypoints."""
    origin, destination = sample_locations
    waypoints = [
        Location(latitude=50.1109, longitude=8.6821, address="Frankfurt, Germany"),
        Location(latitude=48.8566, longitude=2.3522, address="Paris, France")
    ]

    # Mock response
    mock_response = {
        "routes": [{
            "legs": [{
                "distance": {"value": 500000},
                "duration": {"value": 18000},
                "steps": [{
                    "distance": {"value": 500000},
                    "duration": {"value": 18000},
                    "start_location": {"lat": 52.5200, "lng": 13.4050},
                    "end_location": {"lat": 50.1109, "lng": 8.6821}
                }]
            }]
        }]
    }
    service.client.directions.return_value = mock_response

    route = service.calculate_route(origin, destination, waypoints=waypoints)
    assert isinstance(route, RouteSegment)

    # Verify waypoints were passed correctly
    service.client.directions.assert_called_once_with(
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        mode=DEFAULT_MODE,
        units=DEFAULT_UNITS,
        language=DEFAULT_LANGUAGE,
        waypoints=[(wp.latitude, wp.longitude) for wp in waypoints]
    ) 