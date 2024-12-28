"""Repository implementations for route-related entities."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ...domain.entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving
)
from ..models.route_models import (
    RouteModel, LocationModel, TimelineEventModel,
    CountrySegmentModel, EmptyDrivingModel
)
from .base import BaseRepository


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is in UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SQLRouteRepository(BaseRepository[RouteModel]):
    """SQLAlchemy implementation of RouteRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(RouteModel, db)

    def save(self, route: Route) -> Route:
        """Save a route instance."""
        # Create origin and destination locations
        origin_model = LocationModel(
            id=str(uuid4()),
            latitude=route.origin.latitude,
            longitude=route.origin.longitude,
            address=route.origin.address
        )
        destination_model = LocationModel(
            id=str(uuid4()),
            latitude=route.destination.latitude,
            longitude=route.destination.longitude,
            address=route.destination.address
        )

        # Create empty driving
        empty_driving_model = EmptyDrivingModel(
            id=str(uuid4()),
            distance_km=route.empty_driving.distance_km,
            duration_hours=route.empty_driving.duration_hours
        )

        # Create route model
        model = RouteModel(
            id=str(route.id),
            transport_id=str(route.transport_id),
            business_entity_id=str(route.business_entity_id),
            cargo_id=str(route.cargo_id),
            origin=origin_model,
            destination=destination_model,
            pickup_time=_ensure_utc(route.pickup_time),
            delivery_time=_ensure_utc(route.delivery_time),
            empty_driving=empty_driving_model,
            total_distance_km=route.total_distance_km,
            total_duration_hours=route.total_duration_hours,
            is_feasible=route.is_feasible
        )

        # Create timeline events
        for event in route.timeline_events:
            event_location = LocationModel(
                id=str(uuid4()),
                latitude=event.location.latitude,
                longitude=event.location.longitude,
                address=event.location.address
            )
            event_model = TimelineEventModel(
                id=str(event.id),
                route_id=str(route.id),
                type=event.type,
                location=event_location,
                planned_time=_ensure_utc(event.planned_time),
                duration_hours=event.duration_hours,
                event_order=event.event_order
            )
            model.timeline_events.append(event_model)

        # Create country segments
        for segment in route.country_segments:
            start_location = LocationModel(
                id=str(uuid4()),
                latitude=segment.start_location.latitude,
                longitude=segment.start_location.longitude,
                address=segment.start_location.address
            )
            end_location = LocationModel(
                id=str(uuid4()),
                latitude=segment.end_location.latitude,
                longitude=segment.end_location.longitude,
                address=segment.end_location.address
            )
            segment_model = CountrySegmentModel(
                id=str(uuid4()),
                route_id=str(route.id),
                country_code=segment.country_code,
                distance_km=segment.distance_km,
                duration_hours=segment.duration_hours,
                start_location=start_location,
                end_location=end_location
            )
            model.country_segments.append(segment_model)

        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def _to_domain(self, model: RouteModel) -> Route:
        """Convert model to domain entity."""
        return Route(
            id=UUID(model.id),
            transport_id=UUID(model.transport_id),
            business_entity_id=UUID(model.business_entity_id),
            cargo_id=UUID(model.cargo_id),
            origin=Location(
                latitude=model.origin.latitude,
                longitude=model.origin.longitude,
                address=model.origin.address
            ),
            destination=Location(
                latitude=model.destination.latitude,
                longitude=model.destination.longitude,
                address=model.destination.address
            ),
            pickup_time=_ensure_utc(model.pickup_time),
            delivery_time=_ensure_utc(model.delivery_time),
            empty_driving=EmptyDriving(
                distance_km=model.empty_driving.distance_km,
                duration_hours=model.empty_driving.duration_hours
            ),
            timeline_events=[
                TimelineEvent(
                    id=UUID(event.id),
                    type=event.type,
                    location=Location(
                        latitude=event.location.latitude,
                        longitude=event.location.longitude,
                        address=event.location.address
                    ),
                    planned_time=_ensure_utc(event.planned_time),
                    duration_hours=event.duration_hours,
                    event_order=event.event_order
                )
                for event in model.timeline_events
            ],
            country_segments=[
                CountrySegment(
                    country_code=segment.country_code,
                    distance_km=segment.distance_km,
                    duration_hours=segment.duration_hours,
                    start_location=Location(
                        latitude=segment.start_location.latitude,
                        longitude=segment.start_location.longitude,
                        address=segment.start_location.address
                    ),
                    end_location=Location(
                        latitude=segment.end_location.latitude,
                        longitude=segment.end_location.longitude,
                        address=segment.end_location.address
                    )
                )
                for segment in model.country_segments
            ],
            total_distance_km=model.total_distance_km,
            total_duration_hours=model.total_duration_hours,
            is_feasible=model.is_feasible
        ) 