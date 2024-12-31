"""Tests for location domain entity."""
import uuid
import pytest
from pydantic import ValidationError

from backend.domain.entities.location import Location


def test_create_valid_location():
    """Test creating a valid location."""
    # Arrange
    location_data = {
        "id": uuid.uuid4(),
        "latitude": 52.520008,  # Berlin
        "longitude": 13.404954,
        "address": "Berlin, Germany"
    }

    # Act
    location = Location(**location_data)

    # Assert
    assert location.id == location_data["id"]
    assert location.latitude == location_data["latitude"]
    assert location.longitude == location_data["longitude"]
    assert location.address == location_data["address"]


def test_create_location_without_address():
    """Test creating a location without address (valid for intermediate points)."""
    # Arrange & Act
    location = Location(
        id=uuid.uuid4(),
        latitude=52.520008,
        longitude=13.404954
    )

    # Assert
    assert location.latitude == 52.520008
    assert location.longitude == 13.404954
    assert location.address == ""  # Default value


def test_latitude_validation():
    """Test latitude validation."""
    # Arrange
    valid_data = {
        "id": uuid.uuid4(),
        "longitude": 13.404954,
        "address": "Test Address"
    }

    # Act & Assert - Below minimum
    with pytest.raises(ValidationError, match="latitude"):
        Location(**{**valid_data, "latitude": -91.0})

    # Act & Assert - Above maximum
    with pytest.raises(ValidationError, match="latitude"):
        Location(**{**valid_data, "latitude": 91.0})

    # Act & Assert - Edge cases (should pass)
    Location(**{**valid_data, "latitude": -90.0})  # Minimum
    Location(**{**valid_data, "latitude": 90.0})   # Maximum
    Location(**{**valid_data, "latitude": 0.0})    # Equator


def test_longitude_validation():
    """Test longitude validation."""
    # Arrange
    valid_data = {
        "id": uuid.uuid4(),
        "latitude": 52.520008,
        "address": "Test Address"
    }

    # Act & Assert - Below minimum
    with pytest.raises(ValidationError, match="longitude"):
        Location(**{**valid_data, "longitude": -181.0})

    # Act & Assert - Above maximum
    with pytest.raises(ValidationError, match="longitude"):
        Location(**{**valid_data, "longitude": 181.0})

    # Act & Assert - Edge cases (should pass)
    Location(**{**valid_data, "longitude": -180.0})  # Minimum
    Location(**{**valid_data, "longitude": 180.0})   # Maximum
    Location(**{**valid_data, "longitude": 0.0})     # Prime meridian


def test_location_immutability():
    """Test that location instances are immutable."""
    # Arrange
    location = Location(
        id=uuid.uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin, Germany"
    )

    # Act & Assert - Attempt to modify attributes
    with pytest.raises((TypeError, ValidationError)):  # Either error is acceptable
        location.latitude = 53.0

    with pytest.raises((TypeError, ValidationError)):
        location.longitude = 14.0

    with pytest.raises((TypeError, ValidationError)):
        location.address = "New Address"


def test_location_model_dump():
    """Test location model dump functionality."""
    # Arrange
    location_data = {
        "id": uuid.uuid4(),
        "latitude": 52.520008,
        "longitude": 13.404954,
        "address": "Berlin, Germany"
    }
    location = Location(**location_data)

    # Act
    dumped_data = location.model_dump()

    # Assert
    assert dumped_data == location_data


def test_location_coordinate_types():
    """Test that coordinates must be numeric."""
    # Arrange & Act & Assert
    # Invalid string that can't be converted to float
    with pytest.raises(ValidationError):
        Location(
            id=uuid.uuid4(),
            latitude="not a number",
            longitude=13.404954
        )

    with pytest.raises(ValidationError):
        Location(
            id=uuid.uuid4(),
            latitude=52.520008,
            longitude="not a number"
        )

    # None values
    with pytest.raises(ValidationError):
        Location(
            id=uuid.uuid4(),
            latitude=None,
            longitude=13.404954
        )

    with pytest.raises(ValidationError):
        Location(
            id=uuid.uuid4(),
            latitude=52.520008,
            longitude=None
        )

    # Valid string that can be converted to float (should pass)
    location = Location(
        id=uuid.uuid4(),
        latitude="52.520008",
        longitude="13.404954"
    )
    assert location.latitude == 52.520008
    assert location.longitude == 13.404954


def test_location_equality():
    """Test location equality comparison."""
    # Arrange
    loc1 = Location(
        id=uuid.uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin"
    )
    loc2 = Location(
        id=uuid.uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Berlin"
    )
    loc3 = Location(
        id=uuid.uuid4(),
        latitude=52.520008,
        longitude=13.404954,
        address="Different"
    )
    loc4 = Location(
        id=uuid.uuid4(),
        latitude=52.0,
        longitude=13.404954,
        address="Berlin"
    )

    # Assert
    assert loc1 != loc2  # Different IDs
    assert loc1 != loc3  # Different IDs and address
    assert loc1 != loc4  # Different IDs and coordinates 