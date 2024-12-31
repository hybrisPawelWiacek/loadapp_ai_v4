"""Tests for location repository implementations."""
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from backend.domain.entities.location import Location
from backend.infrastructure.repositories.location_repository import SQLLocationRepository


@pytest.fixture
def location() -> Location:
    """Create a sample location."""
    return Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


class TestSQLLocationRepository:
    """Test cases for SQLLocationRepository."""

    def test_save_location(self, db: Session, location: Location):
        """Test saving a location instance."""
        # Arrange
        repo = SQLLocationRepository(db)

        # Act
        saved_location = repo.save(location)

        # Assert
        assert isinstance(saved_location, Location)
        assert saved_location.id == location.id
        assert saved_location.latitude == location.latitude
        assert saved_location.longitude == location.longitude
        assert saved_location.address == location.address

    def test_find_location_by_id(self, db: Session, location: Location):
        """Test finding a location by ID."""
        # Arrange
        repo = SQLLocationRepository(db)
        saved_location = repo.save(location)

        # Act
        found_location = repo.find_by_id(saved_location.id)

        # Assert
        assert found_location is not None
        assert found_location.id == location.id
        assert found_location.latitude == location.latitude
        assert found_location.longitude == location.longitude
        assert found_location.address == location.address

    def test_find_nonexistent_location(self, db: Session):
        """Test finding a location that doesn't exist."""
        # Arrange
        repo = SQLLocationRepository(db)

        # Act
        found_location = repo.find_by_id(uuid4())

        # Assert
        assert found_location is None 