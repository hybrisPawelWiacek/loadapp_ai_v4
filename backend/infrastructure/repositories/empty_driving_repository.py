"""Repository for empty driving records."""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ...domain.entities.route import EmptyDriving
from ..models.route_models import EmptyDrivingModel
from .base import BaseRepository


class SQLEmptyDrivingRepository(BaseRepository[EmptyDrivingModel]):
    """SQLAlchemy implementation of EmptyDrivingRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(EmptyDrivingModel, db)

    def find_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving record by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: EmptyDrivingModel) -> EmptyDriving:
        """Convert model to domain entity."""
        return EmptyDriving(
            id=UUID(model.id),
            distance_km=model.distance_km,
            duration_hours=model.duration_hours
        ) 