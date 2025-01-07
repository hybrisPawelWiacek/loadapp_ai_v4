"""Repository implementation for route-related entities."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ...domain.entities.route import (
    Route, RouteStatus, TimelineEvent, CountrySegment, Location, EmptyDriving, EventStatus, SegmentType
)
from ..models.route_models import (
    RouteModel, TimelineEventModel, CountrySegmentModel, LocationModel, EmptyDrivingModel,
    RouteStatusHistoryModel
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
        try:
            # Convert timeline events
            timeline_events = []
            for event in route.timeline_events:
                event_model = TimelineEventModel(
                    id=str(event.id),
                    route_id=str(route.id),
                    type=event.type,
                    location_id=str(event.location_id),
                    planned_time=event.planned_time,
                    duration_hours=str(event.duration_hours),
                    event_order=event.event_order
                )
                timeline_events.append(event_model)

            # Convert country segments
            country_segments = []
            for segment in route.country_segments:
                segment_model = CountrySegmentModel(
                    id=str(segment.id),
                    route_id=str(route.id),
                    country_code=segment.country_code,
                    segment_type=segment.segment_type.value,
                    distance_km=str(segment.distance_km),
                    duration_hours=str(segment.duration_hours),
                    start_location_id=str(segment.start_location_id),
                    end_location_id=str(segment.end_location_id),
                    segment_order=segment.segment_order
                )
                country_segments.append(segment_model)

            # Create or update route model
            model = self._db.query(RouteModel).filter_by(id=str(route.id)).first()
            if model:
                # Update existing model
                model.transport_id = str(route.transport_id)
                model.business_entity_id = str(route.business_entity_id)
                model.cargo_id = str(route.cargo_id) if route.cargo_id else None
                model.origin_id = str(route.origin_id)
                model.destination_id = str(route.destination_id)
                model.truck_location_id = str(route.truck_location_id)
                model.pickup_time = route.pickup_time
                model.delivery_time = route.delivery_time
                model.empty_driving_id = str(route.empty_driving_id)
                model.total_distance_km = str(route.total_distance_km)
                model.total_duration_hours = str(route.total_duration_hours)
                model.is_feasible = route.is_feasible
                model.status = route.status.value
                model.certifications_validated = route.certifications_validated
                model.operating_countries_validated = route.operating_countries_validated
                model.validation_timestamp = route.validation_timestamp
                model.validation_details = route.validation_details

                # Update timeline events
                self._db.query(TimelineEventModel).filter_by(route_id=str(route.id)).delete()
                model.timeline_events = timeline_events

                # Update country segments
                self._db.query(CountrySegmentModel).filter_by(route_id=str(route.id)).delete()
                model.country_segments = country_segments
            else:
                # Create new model
                model = RouteModel(
                    id=str(route.id),
                    transport_id=str(route.transport_id),
                    business_entity_id=str(route.business_entity_id),
                    cargo_id=str(route.cargo_id) if route.cargo_id else None,
                    origin_id=str(route.origin_id),
                    destination_id=str(route.destination_id),
                    truck_location_id=str(route.truck_location_id),
                    pickup_time=route.pickup_time,
                    delivery_time=route.delivery_time,
                    empty_driving_id=str(route.empty_driving_id),
                    total_distance_km=str(route.total_distance_km),
                    total_duration_hours=str(route.total_duration_hours),
                    is_feasible=route.is_feasible,
                    status=route.status.value,
                    certifications_validated=route.certifications_validated,
                    operating_countries_validated=route.operating_countries_validated,
                    validation_timestamp=route.validation_timestamp,
                    validation_details=route.validation_details,
                    timeline_events=timeline_events,
                    country_segments=country_segments
                )
                self._db.add(model)

            self._db.commit()

            # Return updated route
            return self.find_by_id(route.id)
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to save route: {str(e)}")

    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        try:
            model = self._db.query(RouteModel).filter_by(id=str(id)).first()
            if not model:
                return None
            
            # Sort country segments by segment_order
            model.country_segments.sort(key=lambda x: x.segment_order)
            
            return self._to_entity(model)
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to find route: {str(e)}")

    def find_by_business_entity_id(self, business_entity_id: UUID) -> List[Route]:
        """Find routes by business entity ID."""
        try:
            models = self._db.query(RouteModel).filter_by(business_entity_id=str(business_entity_id)).all()
            for model in models:
                # Sort country segments by segment_order
                model.country_segments.sort(key=lambda x: x.segment_order)
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to find routes by business entity ID: {str(e)}")

    def find_by_cargo_id(self, cargo_id: UUID) -> List[Route]:
        """Find routes by cargo ID."""
        try:
            models = self._db.query(RouteModel).filter_by(cargo_id=str(cargo_id)).all()
            for model in models:
                # Sort country segments by segment_order
                model.country_segments.sort(key=lambda x: x.segment_order)
            return [self._to_entity(model) for model in models]
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to find routes by cargo ID: {str(e)}")

    def get_location_by_id(self, location_id: UUID) -> Optional[Location]:
        """Get a location by ID."""
        try:
            model = self._db.query(LocationModel).filter(LocationModel.id == str(location_id)).first()
            if not model:
                return None
            return Location(
                id=UUID(model.id),
                latitude=float(model.latitude),
                longitude=float(model.longitude),
                address=model.address
            )
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to get location: {str(e)}")

    def find_empty_driving_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving by ID."""
        try:
            model = self._db.query(EmptyDrivingModel).filter(EmptyDrivingModel.id == str(id)).first()
            if not model:
                return None
            return EmptyDriving(
                id=UUID(model.id),
                distance_km=float(model.distance_km),
                duration_hours=float(model.duration_hours)
            )
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to find empty driving: {str(e)}")

    def save_empty_driving(self, empty_driving: EmptyDriving) -> EmptyDriving:
        """Save an empty driving instance."""
        try:
            model = EmptyDrivingModel(
                id=str(empty_driving.id),
                distance_km=str(empty_driving.distance_km),
                duration_hours=str(empty_driving.duration_hours)
            )
            self._db.add(model)
            self._db.commit()
            return empty_driving
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to save empty driving: {str(e)}")

    def _to_entity(self, model: RouteModel) -> Route:
        """Convert SQLAlchemy model to domain entity."""
        try:
            # Convert timeline events to entities
            timeline_events = []
            for event_model in model.timeline_events:
                event = TimelineEvent(
                    id=UUID(event_model.id),
                    route_id=UUID(event_model.route_id),
                    type=event_model.type,
                    location_id=UUID(event_model.location_id),
                    planned_time=event_model.planned_time,
                    duration_hours=float(event_model.duration_hours),
                    event_order=event_model.event_order,
                    status=EventStatus(event_model.status)
                )
                timeline_events.append(event)

            # Convert country segments to entities
            country_segments = []
            for segment_model in model.country_segments:
                segment = CountrySegment(
                    id=UUID(segment_model.id),
                    route_id=UUID(segment_model.route_id),
                    country_code=segment_model.country_code,
                    segment_type=SegmentType.ROUTE if segment_model.segment_type == "ROUTE" else SegmentType.EMPTY_DRIVING,
                    distance_km=float(segment_model.distance_km),
                    duration_hours=float(segment_model.duration_hours),
                    start_location_id=UUID(segment_model.start_location_id),
                    end_location_id=UUID(segment_model.end_location_id),
                    segment_order=segment_model.segment_order
                )
                country_segments.append(segment)

            # Create route entity
            return Route(
                id=UUID(model.id),
                transport_id=UUID(model.transport_id),
                business_entity_id=UUID(model.business_entity_id),
                cargo_id=UUID(model.cargo_id) if model.cargo_id else None,
                origin_id=UUID(model.origin_id),
                destination_id=UUID(model.destination_id),
                truck_location_id=UUID(model.truck_location_id),
                pickup_time=model.pickup_time,
                delivery_time=model.delivery_time,
                empty_driving_id=UUID(model.empty_driving_id) if model.empty_driving_id else None,
                empty_driving=self.find_empty_driving_by_id(UUID(model.empty_driving_id)) if model.empty_driving_id else None,
                total_distance_km=float(model.total_distance_km),
                total_duration_hours=float(model.total_duration_hours),
                is_feasible=model.is_feasible,
                status=RouteStatus(model.status),
                timeline_events=timeline_events,
                country_segments=country_segments,
                certifications_validated=model.certifications_validated,
                operating_countries_validated=model.operating_countries_validated,
                validation_timestamp=model.validation_timestamp,
                validation_details=model.validation_details
            )
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to convert model to entity: {str(e)}")

    def get_status_history(self, route_id: UUID) -> List[RouteStatusHistoryModel]:
        """Get status history for a route."""
        try:
            history = (
                self._db.query(RouteStatusHistoryModel)
                .filter(RouteStatusHistoryModel.route_id == str(route_id))
                .order_by(RouteStatusHistoryModel.timestamp.desc())
                .all()
            )
            return history
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Failed to get route status history: {str(e)}")

    def find_segment_by_id(self, segment_id: UUID) -> Optional[CountrySegment]:
        """Find a country segment by ID."""
        try:
            segment = self._db.query(CountrySegmentModel).filter_by(id=str(segment_id)).first()
            if not segment:
                return None
            return CountrySegment(
                id=UUID(segment.id),
                route_id=UUID(segment.route_id) if segment.route_id else None,
                country_code=segment.country_code,
                segment_type=SegmentType(segment.segment_type),
                distance_km=segment.distance_km,
                duration_hours=segment.duration_hours,
                start_location_id=UUID(segment.start_location_id),
                end_location_id=UUID(segment.end_location_id),
                segment_order=segment.segment_order
            )
        except Exception as e:
            logger.error(f"Failed to find segment by ID {segment_id}: {str(e)}")
            return None 