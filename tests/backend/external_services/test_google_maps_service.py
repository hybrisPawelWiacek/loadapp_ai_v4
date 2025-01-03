"""Unit tests for Google Maps service."""
import pytest
from unittest.mock import patch, Mock, PropertyMock
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
def mock_googlemaps(test_config):
    """Create a mock Google Maps client."""
    with patch("backend.infrastructure.external_services.google_maps_service.googlemaps.Client") as mock:
        mock_instance = Mock()
        mock_instance.directions = Mock()
        mock_instance.distance_matrix = Mock()
        mock_instance.geocode = Mock()
        mock_instance.reverse_geocode = Mock()
        # Set the key property
        type(mock_instance).key = PropertyMock(return_value=test_config.GOOGLE_MAPS.API_KEY)
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_location_repo():
    """Create a mock location repository."""
    mock = Mock()
    mock.save = Mock(side_effect=lambda x: x)  # Return the same location object that was passed
    return mock


@pytest.fixture
def google_maps_service(test_config, mock_googlemaps, mock_location_repo):
    """Create a Google Maps service instance with test configuration."""
    return GoogleMapsService(
        api_key=test_config.GOOGLE_MAPS.API_KEY,
        location_repo=mock_location_repo,
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


def test_initialization(test_config, mock_googlemaps, mock_location_repo):
    """Test service initialization."""
    service = GoogleMapsService(
        api_key=test_config.GOOGLE_MAPS.API_KEY,
        location_repo=mock_location_repo,
        timeout=test_config.GOOGLE_MAPS.TIMEOUT,
        max_retries=test_config.GOOGLE_MAPS.MAX_RETRIES,
        retry_delay=test_config.GOOGLE_MAPS.RETRY_DELAY
    )
    assert service.api_key == test_config.GOOGLE_MAPS.API_KEY
    assert service.mode == DEFAULT_MODE
    assert service.units == DEFAULT_UNITS
    assert service.language == DEFAULT_LANGUAGE


def test_initialization_without_api_key(mock_location_repo):
    """Test service initialization without API key."""
    with pytest.raises(ValueError, match="API key is required"):
        GoogleMapsService(api_key=None, location_repo=mock_location_repo)


def test_calculate_route_success(google_maps_service, sample_locations):
    """Test successful route calculation with multiple country segments."""
    origin, destination = sample_locations

    # Mock response in the format our service expects - Berlin to Paris route
    mock_response = [{
        "legs": [{
            "distance": {"value": 1050000},  # 1050 km in meters
            "duration": {"value": 36000},    # 10 hours in seconds
            "steps": [
                {
                    "distance": {"value": 550000},  # First 550 km in Germany
                    "duration": {"value": 19800},   # 5.5 hours
                    "start_location": {"lat": 52.5200, "lng": 13.4050},  # Berlin
                    "end_location": {"lat": 49.0069, "lng": 8.4037}      # Karlsruhe (near French border)
                },
                {
                    "distance": {"value": 500000},  # 500 km in France
                    "duration": {"value": 16200},   # 4.5 hours
                    "start_location": {"lat": 49.0069, "lng": 8.4037},   # Karlsruhe
                    "end_location": {"lat": 48.8566, "lng": 2.3522}      # Paris
                }
            ]
        }]
    }]

    # Set up the mock to return the response
    google_maps_service._client.directions = Mock(return_value=mock_response)

    # Mock reverse geocoding responses for country detection
    mock_geocoding_responses = [
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Berlin, Germany"}],  # Origin
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}],    # Destination
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Karlsruhe, Germany"}],  # Step 1
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}]        # Step 2
    ]

    # Set up the mock to return the responses in sequence
    google_maps_service._client.reverse_geocode = Mock(side_effect=mock_geocoding_responses)

    # Call calculate_route and unpack the returned tuple
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination)
    
    # Verify the total distance and duration
    assert distance_km == 1050.0
    assert duration_hours == 10.0
    
    # Verify we got three segments (empty driving, German, French)
    assert len(segments) == 3
    
    # Verify the empty driving segment
    empty_segment = segments[0]
    assert empty_segment.country_code == "DE"
    assert abs(empty_segment.distance_km - 200.0) < 0.1  # 200 km
    assert abs(empty_segment.duration_hours - 4.0) < 0.1  # 4 hours
    assert empty_segment.start_location_id == origin.id
    assert empty_segment.end_location_id == origin.id
    
    # Verify the German segment
    german_segment = segments[1]
    assert german_segment.country_code == "DE"
    assert abs(german_segment.distance_km - 550.0) < 0.1  # 550 km
    assert abs(german_segment.duration_hours - 5.5) < 0.1  # 5.5 hours
    assert german_segment.start_location_id == origin.id
    
    # Verify the French segment
    french_segment = segments[2]
    assert french_segment.country_code == "FR"
    assert abs(french_segment.distance_km - 500.0) < 0.1  # 500 km
    assert abs(french_segment.duration_hours - 4.5) < 0.1  # 4.5 hours
    assert french_segment.end_location_id == destination.id


def test_calculate_route_retry_success(google_maps_service, sample_locations):
    """Test successful route calculation after temporary failure."""
    origin, destination = sample_locations

    # Mock response that fails first, then succeeds
    mock_response = [{
        "legs": [{
            "distance": {"value": 1050000},  # 1050 km in meters
            "duration": {"value": 36000},    # 10 hours in seconds
            "steps": [
                {
                    "distance": {"value": 550000},  # First 550 km in Germany
                    "duration": {"value": 19800},   # 5.5 hours
                    "start_location": {"lat": 52.5200, "lng": 13.4050},  # Berlin
                    "end_location": {"lat": 49.0069, "lng": 8.4037}      # Karlsruhe (near French border)
                },
                {
                    "distance": {"value": 500000},  # 500 km in France
                    "duration": {"value": 16200},   # 4.5 hours
                    "start_location": {"lat": 49.0069, "lng": 8.4037},   # Karlsruhe
                    "end_location": {"lat": 48.8566, "lng": 2.3522}      # Paris
                }
            ]
        }]
    }]
    
    # Set up the mock to fail first then succeed
    google_maps_service._client.directions = Mock(side_effect=[Exception("Temporary error"), mock_response])

    # Mock reverse geocoding responses for country detection
    mock_geocoding_responses = [
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Berlin, Germany"}],  # Origin
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}],    # Destination
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Karlsruhe, Germany"}],  # Step 1
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}]        # Step 2
    ]

    # Set up the mock to return the responses in sequence
    google_maps_service._client.reverse_geocode = Mock(side_effect=mock_geocoding_responses)

    # Call calculate_route and unpack the returned tuple
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination)
    
    # Verify the total distance and duration
    assert distance_km == 1050.0
    assert duration_hours == 10.0
    
    # Verify we got three segments (empty driving, German, French)
    assert len(segments) == 3
    
    # Verify the empty driving segment
    empty_segment = segments[0]
    assert empty_segment.country_code == "DE"
    assert abs(empty_segment.distance_km - 200.0) < 0.1  # 200 km
    assert abs(empty_segment.duration_hours - 4.0) < 0.1  # 4 hours
    assert empty_segment.start_location_id == origin.id
    assert empty_segment.end_location_id == origin.id
    
    # Verify the German segment
    german_segment = segments[1]
    assert german_segment.country_code == "DE"
    assert abs(german_segment.distance_km - 550.0) < 0.1  # 550 km
    assert abs(german_segment.duration_hours - 5.5) < 0.1  # 5.5 hours
    assert german_segment.start_location_id == origin.id
    
    # Verify the French segment
    french_segment = segments[2]
    assert french_segment.country_code == "FR"
    assert abs(french_segment.distance_km - 500.0) < 0.1  # 500 km
    assert abs(french_segment.duration_hours - 4.5) < 0.1  # 4.5 hours
    assert french_segment.end_location_id == destination.id


def test_calculate_route_with_departure_time(google_maps_service, sample_locations):
    """Test route calculation with departure time."""
    origin, destination = sample_locations
    departure_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Mock response in the format our service expects
    mock_response = [{
        "legs": [{
            "distance": {"value": 1050000},  # 1050 km in meters
            "duration": {"value": 36000},    # 10 hours in seconds
            "steps": [
                {
                    "distance": {"value": 550000},  # First 550 km in Germany
                    "duration": {"value": 19800},   # 5.5 hours
                    "start_location": {"lat": 52.5200, "lng": 13.4050},  # Berlin
                    "end_location": {"lat": 49.0069, "lng": 8.4037}      # Karlsruhe (near French border)
                },
                {
                    "distance": {"value": 500000},  # 500 km in France
                    "duration": {"value": 16200},   # 4.5 hours
                    "start_location": {"lat": 49.0069, "lng": 8.4037},   # Karlsruhe
                    "end_location": {"lat": 48.8566, "lng": 2.3522}      # Paris
                }
            ]
        }]
    }]

    # Set up the mock to return the response
    google_maps_service._client.directions = Mock(return_value=mock_response)

    # Mock reverse geocoding responses for country detection
    mock_geocoding_responses = [
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Berlin, Germany"}],  # Origin
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}],    # Destination
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Karlsruhe, Germany"}],  # Step 1
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}]        # Step 2
    ]

    # Set up the mock to return the responses in sequence
    google_maps_service._client.reverse_geocode = Mock(side_effect=mock_geocoding_responses)

    # Call calculate_route with departure time
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination, departure_time=departure_time)
    
    # Verify the total distance and duration
    assert distance_km == 1050.0
    assert duration_hours == 10.0
    
    # Verify we got three segments (empty driving, German, French)
    assert len(segments) == 3
    
    # Verify the empty driving segment
    empty_segment = segments[0]
    assert empty_segment.country_code == "DE"
    assert abs(empty_segment.distance_km - 200.0) < 0.1  # 200 km
    assert abs(empty_segment.duration_hours - 4.0) < 0.1  # 4 hours
    assert empty_segment.start_location_id == origin.id
    assert empty_segment.end_location_id == origin.id
    
    # Verify the German segment
    german_segment = segments[1]
    assert german_segment.country_code == "DE"
    assert abs(german_segment.distance_km - 550.0) < 0.1  # 550 km
    assert abs(german_segment.duration_hours - 5.5) < 0.1  # 5.5 hours
    assert german_segment.start_location_id == origin.id
    
    # Verify the French segment
    french_segment = segments[2]
    assert french_segment.country_code == "FR"
    assert abs(french_segment.distance_km - 500.0) < 0.1  # 500 km
    assert abs(french_segment.duration_hours - 4.5) < 0.1  # 4.5 hours
    assert french_segment.end_location_id == destination.id
    
    # Verify the API was called with departure_time
    google_maps_service._client.directions.assert_called_once()
    call_kwargs = google_maps_service._client.directions.call_args[1]
    assert call_kwargs.get("departure_time") == departure_time


def test_calculate_route_no_routes_found(google_maps_service, sample_locations):
    """Test handling when no routes are found."""
    origin, destination = sample_locations
    google_maps_service._client.directions.return_value = []

    with pytest.raises(GoogleMapsServiceError, match="No route found"):
        google_maps_service.calculate_route(origin, destination)


def test_calculate_route_api_error(google_maps_service, sample_locations):
    """Test handling of API errors."""
    origin, destination = sample_locations
    google_maps_service._client.directions.side_effect = Exception("API Error")

    with pytest.raises(GoogleMapsServiceError, match="Failed to calculate route: API Error"):
        google_maps_service.calculate_route(origin, destination)


def test_calculate_route_invalid_locations(google_maps_service):
    """Test handling of invalid locations."""
    # Test invalid latitude
    with pytest.raises(ValidationError) as exc_info:
        Location(
            id=uuid4(),
            latitude=91.0,  # Invalid latitude
            longitude=0.0,
            address="Invalid Location"
        )
    assert "Input should be less than or equal to 90" in str(exc_info.value)

    # Test invalid longitude
    with pytest.raises(ValidationError) as exc_info:
        Location(
            id=uuid4(),
            latitude=0.0,
            longitude=181.0,  # Invalid longitude
            address="Invalid Location"
        )
    assert "Input should be less than or equal to 180" in str(exc_info.value)

    # Test with None values
    with pytest.raises(ValidationError) as exc_info:
        Location(
            id=uuid4(),
            latitude=None,
            longitude=None,
            address="Invalid Location"
        )
    assert "Input should be a valid number" in str(exc_info.value)


def test_calculate_route_invalid_avoid_options(google_maps_service, sample_locations):
    """Test handling of invalid avoid options."""
    origin, destination = sample_locations
    invalid_avoid = ["invalid_option"]

    # Mock response for the invalid avoid option case
    mock_response = [{
        "legs": [{
            "distance": {"value": 1050000},
            "duration": {"value": 36000},
            "steps": [
                {
                    "distance": {"value": 550000},
                    "duration": {"value": 19800},
                    "start_location": {"lat": 52.5200, "lng": 13.4050},
                    "end_location": {"lat": 49.0069, "lng": 8.4037}
                },
                {
                    "distance": {"value": 500000},
                    "duration": {"value": 16200},
                    "start_location": {"lat": 49.0069, "lng": 8.4037},
                    "end_location": {"lat": 48.8566, "lng": 2.3522}
                }
            ]
        }]
    }]

    google_maps_service._client.directions = Mock(return_value=mock_response)

    # Mock reverse geocoding responses
    mock_geocoding_responses = [
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Berlin, Germany"}],
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}],
        [{"address_components": [{"types": ["country"], "short_name": "DE"}], "formatted_address": "Karlsruhe, Germany"}],
        [{"address_components": [{"types": ["country"], "short_name": "FR"}], "formatted_address": "Paris, France"}]
    ]
    google_maps_service._client.reverse_geocode = Mock(side_effect=mock_geocoding_responses)

    # The service should handle invalid avoid options gracefully
    distance_km, duration_hours, segments = google_maps_service.calculate_route(origin, destination, avoid=invalid_avoid)
    
    assert distance_km == 1050.0
    assert duration_hours == 10.0
    assert len(segments) == 3 