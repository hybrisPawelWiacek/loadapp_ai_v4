"""Tests for Google Maps service."""
import pytest
from unittest.mock import Mock, patch
from googlemaps.exceptions import ApiError, TransportError, Timeout
import uuid
from datetime import datetime, timedelta

from backend.domain.entities.route import Route, RouteSegment, EmptyDriving
from backend.infrastructure.external_services.google_maps_service import (
    GoogleMapsService,
    GoogleMapsServiceError
)
from backend.domain.entities.location import Location

@pytest.fixture
def mock_gmaps_client():
    return Mock()

@pytest.fixture
def service(mock_gmaps_client):
    with patch('googlemaps.Client') as mock_client:
        mock_client.return_value = mock_gmaps_client
        service = GoogleMapsService(api_key='fake_api_key')
        return service

@pytest.fixture
def sample_locations():
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin")
    destination = Location(latitude=48.8566, longitude=2.3522, address="Paris")
    return origin, destination

def test_calculate_route_success(service, mock_gmaps_client, sample_locations):
    origin, destination = sample_locations
    
    # Mock successful API response
    mock_gmaps_client.directions.return_value = {
        "routes": [{
            "legs": [{
                "distance": {"value": 1000000},  # 1000 km in meters
                "duration": {"value": 36000},    # 10 hours in seconds
                "steps": []
            }]
        }]
    }

    result = service.calculate_route(origin, destination)
    
    assert isinstance(result, RouteSegment)
    assert result.distance_km == 1000.0  # km
    assert result.duration_hours == 10.0  # hours
    assert result.start_location == origin
    assert result.end_location == destination

def test_calculate_route_api_error(service, mock_gmaps_client, sample_locations):
    origin, destination = sample_locations
    mock_gmaps_client.directions.side_effect = ApiError("API Error")
    
    with pytest.raises(GoogleMapsServiceError, match="Failed to calculate route: API Error"):
        service.calculate_route(origin, destination)

def test_calculate_route_retry_success(service, mock_gmaps_client, sample_locations):
    origin, destination = sample_locations
    
    # Mock API failure then success
    mock_gmaps_client.directions.side_effect = [
        TransportError("Temporary error"),
        {
            "routes": [{
                "legs": [{
                    "distance": {"value": 1000000},
                    "duration": {"value": 36000},
                    "steps": []
                }]
            }]
        }
    ]

    result = service.calculate_route(origin, destination)
    assert isinstance(result, RouteSegment)
    assert result.distance_km == 1000.0
    assert result.duration_hours == 10.0

def test_request_retry_timeout(service, mock_gmaps_client, sample_locations):
    origin, destination = sample_locations
    mock_gmaps_client.directions.side_effect = TransportError("Persistent error")
    
    with pytest.raises(GoogleMapsServiceError, match="Failed to calculate route: Persistent error"):
        service.calculate_route(origin, destination)
    
    # Verify retry attempts (from _make_request method)
    assert mock_gmaps_client.directions.call_count >= 1

def test_get_country_segments_success(service, mock_gmaps_client, sample_locations):
    """Test successful retrieval of country segments."""
    origin, destination = sample_locations
    
    # Mock directions API response
    mock_gmaps_client.directions.return_value = [{
        "legs": [{
            "steps": [
                {
                    "distance": {"value": 50000},  # 50 km
                    "duration": {"value": 3600},   # 1 hour
                    "start_location": {"lat": 52.5200, "lng": 13.4050},
                    "end_location": {"lat": 51.0, "lng": 12.0}
                },
                {
                    "distance": {"value": 100000},  # 100 km
                    "duration": {"value": 7200},    # 2 hours
                    "start_location": {"lat": 51.0, "lng": 12.0},
                    "end_location": {"lat": 48.8566, "lng": 2.3522}
                }
            ]
        }]
    }]
    
    # Mock reverse geocoding responses for all calls
    mock_gmaps_client.reverse_geocode.side_effect = [
        # First step end location (Germany)
        [{"address_components": [{"types": ["country"], "short_name": "DE"}]}],
        # Second step end location (France)
        [{"address_components": [{"types": ["country"], "short_name": "FR"}]}],
        # Second step end location again (for next step check)
        [{"address_components": [{"types": ["country"], "short_name": "FR"}]}]
    ]
    
    segments = service.get_country_segments(origin, destination)
    
    assert len(segments) == 2
    
    # First segment (Germany)
    assert segments[0].country_code == "DE"
    assert segments[0].distance_km == 50.0
    assert segments[0].duration_hours == 1.0
    assert segments[0].start_location.latitude == 52.5200
    assert segments[0].start_location.longitude == 13.4050
    assert segments[0].end_location.latitude == 51.0
    assert segments[0].end_location.longitude == 12.0
    
    # Second segment (France)
    assert segments[1].country_code == "FR"
    assert segments[1].distance_km == 100.0
    assert segments[1].duration_hours == 2.0
    assert segments[1].start_location.latitude == 51.0
    assert segments[1].start_location.longitude == 12.0
    assert segments[1].end_location.latitude == 48.8566
    assert segments[1].end_location.longitude == 2.3522
    
    # Verify API calls
    mock_gmaps_client.directions.assert_called_once()
    assert mock_gmaps_client.reverse_geocode.call_count == 3

def test_get_country_segments_invalid_location(service, mock_gmaps_client):
    """Test handling of invalid location data."""
    # Test with None values
    with pytest.raises(ValueError) as exc_info:
        service.get_country_segments(None, None)
    assert str(exc_info.value) == "Origin and destination must be Location objects"
        
    # Test with invalid location objects
    invalid_origin = {"latitude": 0, "longitude": 0}  # Not a Location object
    invalid_destination = {"latitude": 1, "longitude": 1}  # Not a Location object
    
    with pytest.raises(ValueError) as exc_info:
        service.get_country_segments(invalid_origin, invalid_destination)
    assert str(exc_info.value) == "Origin and destination must be Location objects"

def test_get_country_segments_api_error(service, mock_gmaps_client, sample_locations):
    """Test handling of API errors."""
    origin, destination = sample_locations
    mock_gmaps_client.directions.side_effect = ApiError("API Error")
    
    with pytest.raises(GoogleMapsServiceError):
        service.get_country_segments(origin, destination) 