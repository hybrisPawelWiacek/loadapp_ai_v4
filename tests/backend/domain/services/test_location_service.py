"""Tests for location service."""
from uuid import uuid4
from unittest.mock import Mock

import pytest

from backend.domain.entities.location import Location
from backend.domain.services.location_service import LocationService


@pytest.fixture
def mock_location():
    """Create a mock location."""
    return Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


@pytest.fixture
def mock_location_repo():
    """Create a mock location repository."""
    repo = Mock()
    repo.save = Mock(side_effect=lambda x: x)  # Return the same location
    repo.find_by_id = Mock(return_value=None)  # Default to not found
    return repo


@pytest.fixture
def mock_maps_service():
    """Create a mock Google Maps service."""
    service = Mock()
    service.geocode = Mock()  # Will be configured in individual tests
    return service


@pytest.fixture
def location_service(mock_location_repo, mock_maps_service):
    """Create a location service instance."""
    return LocationService(
        location_repo=mock_location_repo,
        maps_service=mock_maps_service
    )


class TestLocationService:
    """Test cases for LocationService."""

    def test_create_location_success(self, location_service, mock_location, mock_maps_service):
        """Test successful location creation."""
        # Arrange
        mock_maps_service.geocode.return_value = mock_location
        address = "Berlin, Germany"

        # Act
        location = location_service.create_location(address)

        # Assert
        assert location == mock_location
        mock_maps_service.geocode.assert_called_once_with(address)

    def test_create_location_geocoding_failure(self, location_service, mock_maps_service):
        """Test location creation with geocoding failure."""
        # Arrange
        mock_maps_service.geocode.side_effect = ValueError("Failed to geocode")
        address = "Invalid Address"

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to geocode"):
            location_service.create_location(address)

    def test_get_location_found(self, location_service, mock_location, mock_location_repo):
        """Test getting an existing location."""
        # Arrange
        mock_location_repo.find_by_id.return_value = mock_location

        # Act
        location = location_service.get_location(mock_location.id)

        # Assert
        assert location == mock_location
        mock_location_repo.find_by_id.assert_called_once_with(mock_location.id)

    def test_get_location_not_found(self, location_service):
        """Test getting a non-existent location."""
        # Arrange
        location_id = uuid4()

        # Act
        location = location_service.get_location(location_id)

        # Assert
        assert location is None

    def test_validate_location_valid(self, location_service, mock_location, mock_maps_service):
        """Test validating a valid location."""
        # Arrange
        mock_maps_service.geocode.return_value = mock_location
        address = "Berlin, Germany"

        # Act
        result = location_service.validate_location(address)

        # Assert
        assert result["valid"] is True
        assert result["coordinates"]["latitude"] == mock_location.latitude
        assert result["coordinates"]["longitude"] == mock_location.longitude
        assert result["formatted_address"] == mock_location.address

    def test_validate_location_invalid(self, location_service, mock_maps_service):
        """Test validating an invalid location."""
        # Arrange
        mock_maps_service.geocode.side_effect = ValueError("Invalid address")
        address = "Invalid Address"

        # Act
        result = location_service.validate_location(address)

        # Assert
        assert result["valid"] is False
        assert "error" in result 