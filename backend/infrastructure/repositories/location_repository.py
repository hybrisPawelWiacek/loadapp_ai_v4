"""Repository implementation for location-related entities."""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ...domain.entities.location import Location
from ..models.route_models import LocationModel
from .base import BaseRepository


class SQLLocationRepository(BaseRepository[LocationModel]):
    """SQLAlchemy implementation of LocationRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(LocationModel, db)

    def save(self, location: Location) -> Location:
        """Save a location instance."""
        model = LocationModel(
            id=str(location.id),
            latitude=str(location.latitude),  # Convert to string for SQLite
            longitude=str(location.longitude),  # Convert to string for SQLite
            address=location.address
        )
        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Location]:
        """Find a location by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: LocationModel) -> Location:
        """Convert model to domain entity."""
        return Location(
            id=UUID(model.id),
            latitude=float(model.latitude),  # Convert back to float
            longitude=float(model.longitude),  # Convert back to float
            address=model.address
        ) 