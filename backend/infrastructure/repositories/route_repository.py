"""Repository implementation for route-related entities."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ...domain.entities.route import (
    Route, RouteStatus, TimelineEvent, CountrySegment, Location, EmptyDriving
)
from ..models.route_models import (
    RouteModel, TimelineEventModel, CountrySegmentModel, LocationModel, EmptyDrivingModel
)
from .base import BaseRepository


class SQLEmptyDrivingRepository(BaseRepository[EmptyDrivingModel]):
    """SQLAlchemy implementation of EmptyDrivingRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(EmptyDrivingModel, db)

    def find_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving by ID."""
        model = self.get(str(id))
        if not model:
            return None
        return EmptyDriving(
            id=UUID(model.id),
            distance_km=float(model.distance_km),
            duration_hours=float(model.duration_hours)
        )


class SQLRouteRepository(BaseRepository[RouteModel]):
    """SQLAlchemy implementation of RouteRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(RouteModel, db)

    def save(self, route: Route) -> Route:
        """Save a route instance."""
        # Create or update route model
        model = self.get(str(route.id))
        if not model:
            model = RouteModel(
                id=str(route.id),
                transport_id=str(route.transport_id),
                business_entity_id=str(route.business_entity_id),
                cargo_id=str(route.cargo_id) if route.cargo_id else None,
                origin_id=str(route.origin_id),
                destination_id=str(route.destination_id),
                pickup_time=route.pickup_time,
                delivery_time=route.delivery_time,
                empty_driving_id=str(route.empty_driving_id) if route.empty_driving_id else None,
                total_distance_km=str(route.total_distance_km),
                total_duration_hours=str(route.total_duration_hours),
                is_feasible=route.is_feasible,
                status=route.status.value
            )
            self._db.add(model)
        else:
            # Update existing model
            model.transport_id = str(route.transport_id)
            model.business_entity_id = str(route.business_entity_id)
            model.cargo_id = str(route.cargo_id) if route.cargo_id else None
            model.origin_id = str(route.origin_id)
            model.destination_id = str(route.destination_id)
            model.pickup_time = route.pickup_time
            model.delivery_time = route.delivery_time
            model.empty_driving_id = str(route.empty_driving_id) if route.empty_driving_id else None
            model.total_distance_km = str(route.total_distance_km)
            model.total_duration_hours = str(route.total_duration_hours)
            model.is_feasible = route.is_feasible
            model.status = route.status.value

        # Clear existing timeline events and country segments
        model.timeline_events = []
        model.country_segments = []

        # Add timeline events
        for event in route.timeline_events:
            event_model = TimelineEventModel(
                id=str(event.id),
                route_id=str(route.id),
                type=event.type,
                location_id=str(event.location.id),
                planned_time=event.planned_time,
                duration_hours=str(event.duration_hours),
                event_order=event.event_order
            )
            model.timeline_events.append(event_model)

        # Add country segments
        for segment in route.country_segments:
            segment_model = CountrySegmentModel(
                id=str(uuid4()),  # Generate new ID for segments
                route_id=str(route.id),
                country_code=segment.country_code,
                distance_km=str(segment.distance_km),
                duration_hours=str(segment.duration_hours),
                start_location_id=str(segment.start_location.id),
                end_location_id=str(segment.end_location.id)
            )
            model.country_segments.append(segment_model)

        self._db.commit()
        return self._to_domain(model)

    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def find_by_business_entity_id(self, business_entity_id: UUID) -> List[Route]:
        """Find routes by business entity ID."""
        models = self.list(business_entity_id=str(business_entity_id))
        return [self._to_domain(model) for model in models]

    def get_location_by_id(self, location_id: UUID) -> Optional[Location]:
        """Get a location by ID."""
        model = self._db.query(LocationModel).filter(LocationModel.id == str(location_id)).first()
        if not model:
            return None
        return Location(
            id=UUID(model.id),
            latitude=float(model.latitude),
            longitude=float(model.longitude),
            address=model.address
        )

    def find_empty_driving_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving by ID."""
        model = self._db.query(EmptyDrivingModel).filter(EmptyDrivingModel.id == str(id)).first()
        if not model:
            return None
        return EmptyDriving(
            id=UUID(model.id),
            distance_km=float(model.distance_km),
            duration_hours=float(model.duration_hours)
        )

    def _to_domain(self, model: RouteModel) -> Route:
        """Convert model to domain entity."""
        # Convert timeline events
        timeline_events = []
        for event_model in model.timeline_events:
            location = Location(
                id=UUID(event_model.location.id),
                latitude=float(event_model.location.latitude),
                longitude=float(event_model.location.longitude),
                address=event_model.location.address
            )
            event = TimelineEvent(
                id=UUID(event_model.id),
                type=event_model.type,
                location=location,
                planned_time=event_model.planned_time,
                duration_hours=float(event_model.duration_hours),
                event_order=event_model.event_order
            )
            timeline_events.append(event)

        # Convert country segments
        country_segments = []
        for segment_model in model.country_segments:
            start_location = Location(
                id=UUID(segment_model.start_location.id),
                latitude=float(segment_model.start_location.latitude),
                longitude=float(segment_model.start_location.longitude),
                address=segment_model.start_location.address
            )
            end_location = Location(
                id=UUID(segment_model.end_location.id),
                latitude=float(segment_model.end_location.latitude),
                longitude=float(segment_model.end_location.longitude),
                address=segment_model.end_location.address
            )
            segment = CountrySegment(
                country_code=segment_model.country_code,
                distance_km=float(segment_model.distance_km),
                duration_hours=float(segment_model.duration_hours),
                start_location=start_location,
                end_location=end_location
            )
            country_segments.append(segment)

        return Route(
            id=UUID(model.id),
            transport_id=UUID(model.transport_id),
            business_entity_id=UUID(model.business_entity_id),
            cargo_id=UUID(model.cargo_id) if model.cargo_id else None,
            origin_id=UUID(model.origin_id),
            destination_id=UUID(model.destination_id),
            pickup_time=model.pickup_time,
            delivery_time=model.delivery_time,
            empty_driving_id=UUID(model.empty_driving_id) if model.empty_driving_id else None,
            total_distance_km=float(model.total_distance_km),
            total_duration_hours=float(model.total_duration_hours),
            is_feasible=model.is_feasible,
            status=RouteStatus(model.status),
            timeline_events=timeline_events,
            country_segments=country_segments
        ) 