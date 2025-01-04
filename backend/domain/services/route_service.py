"""Route service for managing route-related business logic."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Protocol, Tuple
from uuid import UUID, uuid4
import structlog

from ..entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving, RouteStatus, EventStatus
)

logger = structlog.get_logger(__name__)

def _log_route_creation(transport_id: UUID, origin_id: UUID, destination_id: UUID, pickup_time: datetime, delivery_time: datetime) -> None:
    """Log route creation details."""
    logger.info("Creating new route",
        transport_id=str(transport_id),
        origin_id=str(origin_id),
        destination_id=str(destination_id),
        pickup_time=pickup_time.isoformat(),
        delivery_time=delivery_time.isoformat()
    )

def _log_route_update(route: Route, action: str) -> None:
    """Log route update details."""
    logger.info(f"Route {action}",
        route_id=str(route.id),
        transport_id=str(route.transport_id),
        status=route.status.value if route.status else None
    )

def _log_timeline_generation(origin: Location, destination: Location, segments: List[CountrySegment], events: List[TimelineEvent]) -> None:
    """Log timeline generation details."""
    logger.debug("Generated timeline events",
        origin_address=origin.address,
        destination_address=destination.address,
        segment_count=len(segments),
        event_count=len(events)
    )


class LocationRepository(Protocol):
    """Repository interface for Location entity."""
    def find_by_id(self, id: UUID) -> Optional[Location]:
        """Find a location by ID."""
        ...


class RouteCalculationPort(Protocol):
    """External service port for route calculations."""
    def calculate_route(
        self,
        origin: Location,
        destination: Location
    ) -> tuple[float, float, List[CountrySegment]]:
        """Calculate route details and country segments."""
        ...


class RouteRepository(Protocol):
    """Repository interface for Route entity."""
    def save(self, route: Route) -> Route:
        """Save a route instance."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        ...

    def save_empty_driving(self, empty_driving: EmptyDriving) -> EmptyDriving:
        """Save empty driving instance."""
        ...


class RouteService:
    """Service for managing route-related business logic."""

    def __init__(
        self,
        route_repo: RouteRepository,
        route_calculator: RouteCalculationPort,
        location_repo: LocationRepository
    ):
        self._route_repo = route_repo
        self._route_calculator = route_calculator
        self._location_repo = location_repo

    def create_route(
        self,
        transport_id: UUID,
        business_entity_id: UUID,
        cargo_id: UUID,
        origin_id: UUID,
        destination_id: UUID,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> Route:
        """Create a new route."""
        _log_route_creation(transport_id, origin_id, destination_id, pickup_time, delivery_time)

        # Fetch locations
        origin = self._location_repo.find_by_id(origin_id)
        destination = self._location_repo.find_by_id(destination_id)
        if not origin or not destination:
            logger.error("Location not found", 
                origin_id=str(origin_id), 
                destination_id=str(destination_id)
            )
            raise ValueError("Origin or destination location not found")

        # Calculate route
        total_distance_km, total_duration_hours, segments = self._route_calculator.calculate_route(
            origin, destination
        )

        # Create empty driving
        empty_driving = EmptyDriving(
            id=uuid4(),
            distance_km=200.0,  # Default values
            duration_hours=4.0
        )
        saved_empty_driving = self._route_repo.save_empty_driving(empty_driving)

        # Generate timeline
        timeline_events = self._generate_timeline_events(
            origin, destination, pickup_time, delivery_time,
            uuid4(), segments
        )
        _log_timeline_generation(origin, destination, segments, timeline_events)

        # Create route
        route = Route(
            id=uuid4(),
            transport_id=transport_id,
            business_entity_id=business_entity_id,
            cargo_id=cargo_id,
            origin_id=origin_id,
            destination_id=destination_id,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            empty_driving_id=saved_empty_driving.id,
            total_distance_km=total_distance_km + saved_empty_driving.distance_km,
            total_duration_hours=total_duration_hours + saved_empty_driving.duration_hours,
            is_feasible=True,
            status=RouteStatus.DRAFT,
            timeline_events=timeline_events,
            country_segments=segments,
            validation_details={}  # Initialize with empty dictionary
        )

        saved_route = self._route_repo.save(route)
        _log_route_update(saved_route, "created")
        return saved_route

    def _generate_timeline_events(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        route_id: UUID,
        segments: Optional[List[CountrySegment]]
    ) -> List[TimelineEvent]:
        """Generate timeline events for a route."""
        logger.debug("Generating timeline events",
            route_id=str(route_id),
            pickup_time=pickup_time.isoformat(),
            delivery_time=delivery_time.isoformat(),
            segment_count=len(segments) if segments else 0
        )

        total_duration = delivery_time - pickup_time
        mid_point = pickup_time + (total_duration / 2)

        events = [
            # Pickup event
            TimelineEvent(
                id=uuid4(),
                route_id=route_id,
                type="pickup",
                location_id=origin.id,
                planned_time=pickup_time,
                duration_hours=1.0,
                event_order=1,
                status=EventStatus.PENDING
            )
        ]

        # Rest event - use first segment's end location or origin if no segments
        rest_location_id = origin.id  # Default to origin
        if segments and len(segments) > 0:
            # Get the end location of the first segment
            rest_location_id = segments[0].end_location_id

        events.append(
            TimelineEvent(
                id=uuid4(),
                route_id=route_id,
                type="rest",
                location_id=rest_location_id,
                planned_time=mid_point,
                duration_hours=1.0,
                event_order=2,
                status=EventStatus.PENDING
            )
        )

        # Delivery event
        events.append(
            TimelineEvent(
                id=uuid4(),
                route_id=route_id,
                type="delivery",
                location_id=destination.id,
                planned_time=delivery_time,
                duration_hours=1.0,
                event_order=3,
                status=EventStatus.PENDING
            )
        )

        _log_timeline_generation(origin, destination, segments or [], events)
        return events

    def get_route(self, route_id: UUID) -> Optional[Route]:
        """Retrieve a route by ID."""
        try:
            return self._route_repo.find_by_id(route_id)
        except Exception as e:
            raise ValueError(f"Failed to get route: {str(e)}")

    def validate_route_feasibility(self, route: Route) -> bool:
        """
        Validate if route is feasible.
        For PoC, always returns True.
        """
        return True  # Simplified for PoC
        
    def handle_cargo_status_change(self, cargo_id: UUID, new_status: str) -> None:
        """
        Handle changes in cargo status and update route status accordingly.
        
        Args:
            cargo_id: ID of the cargo that changed status
            new_status: New status of the cargo
        """
        try:
            # Find route by cargo ID
            routes = self._route_repo.find_by_cargo_id(cargo_id)
            if not routes:
                return
                
            # Update route status based on cargo status
            for route in routes:
                if new_status == "in_transit":
                    route.status = RouteStatus.IN_PROGRESS
                    self._update_timeline_events_for_transit(route)
                elif new_status == "delivered":
                    route.status = RouteStatus.COMPLETED
                    self._update_timeline_events_for_completion(route)
                elif new_status == "cancelled":
                    route.status = RouteStatus.CANCELLED
                    self._update_timeline_events_for_cancellation(route)
                self._route_repo.save(route)
        except Exception as e:
            raise ValueError(f"Failed to handle cargo status change: {str(e)}")

    def _update_timeline_events_for_transit(self, route: Route) -> None:
        """Update timeline events when route enters transit state."""
        current_time = datetime.now(timezone.utc)
        
        # Set pickup event to in_progress
        pickup_event = next((event for event in route.timeline_events 
                           if event.type == "pickup"), None)
        if pickup_event:
            pickup_event.status = EventStatus.IN_PROGRESS
            pickup_event.actual_time = current_time

        # Set other events to pending
        for event in route.timeline_events:
            if event.type != "pickup":
                event.status = EventStatus.PENDING
                event.actual_time = None

    def _update_timeline_events_for_completion(self, route: Route) -> None:
        """Update timeline events when route is completed."""
        current_time = datetime.now(timezone.utc)
        
        # Mark all events as completed
        for event in route.timeline_events:
            event.status = EventStatus.COMPLETED
            if not event.actual_time:  # Only set if not already set
                event.actual_time = current_time

    def _update_timeline_events_for_cancellation(self, route: Route) -> None:
        """Update timeline events when route is cancelled."""
        # Mark incomplete events as cancelled
        for event in route.timeline_events:
            if event.status != EventStatus.COMPLETED:
                event.status = EventStatus.CANCELLED
                event.actual_time = None 