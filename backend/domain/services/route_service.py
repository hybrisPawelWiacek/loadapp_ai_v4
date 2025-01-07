"""Route service for managing route-related business logic."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Protocol, Tuple, Dict, Any
from uuid import UUID, uuid4
import structlog

from ..entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving, RouteStatus, EventStatus, SegmentType
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
    ) -> tuple[float, float, List[CountrySegment], List[List[float]]]:
        """Calculate route details, country segments, and route polyline."""
        ...

    def calculate_empty_driving(
        self,
        truck_location: Location,
        origin: Location
    ) -> tuple[float, float]:
        """Calculate empty driving distance and duration."""
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
        delivery_time: datetime,
        truck_location_id: UUID
    ) -> Route:
        """Create a new route."""
        _log_route_creation(transport_id, origin_id, destination_id, pickup_time, delivery_time)

        # Fetch locations
        origin = self._location_repo.find_by_id(origin_id)
        destination = self._location_repo.find_by_id(destination_id)
        truck_location = self._location_repo.find_by_id(truck_location_id)
        if not origin or not destination or not truck_location:
            logger.error("Location not found", 
                origin_id=str(origin_id), 
                destination_id=str(destination_id),
                truck_location_id=str(truck_location_id)
            )
            raise ValueError("Origin, destination, or truck location not found")

        # Calculate main route
        total_distance_km, total_duration_hours, segments, route_polyline = self._route_calculator.calculate_route(
            origin, destination
        )

        # Calculate empty driving if truck location is provided
        empty_driving = None
        empty_distance_km = 0.0
        empty_duration_hours = 0.0
        if truck_location_id:
            empty_distance_km, empty_duration_hours = self._route_calculator.calculate_empty_driving(
                truck_location, origin
            )
            empty_driving = EmptyDriving(
                id=uuid4(),
                distance_km=empty_distance_km,
                duration_hours=empty_duration_hours
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
            truck_location_id=truck_location_id,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            empty_driving_id=saved_empty_driving.id if saved_empty_driving else None,
            empty_driving=saved_empty_driving,
            total_distance_km=total_distance_km + empty_distance_km,
            total_duration_hours=total_duration_hours + empty_duration_hours,
            is_feasible=True,
            status=RouteStatus.DRAFT,
            timeline_events=timeline_events,
            country_segments=segments,
            route_polyline=route_polyline,
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

    def validate_route_creation(
        self,
        transport_id: UUID,
        cargo_id: UUID,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate route creation parameters.
        
        Args:
            transport_id: ID of the transport to use
            cargo_id: ID of the cargo to transport
            pickup_time: Planned pickup time
            delivery_time: Planned delivery time
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        logger.debug("Validating route creation parameters",
                    transport_id=str(transport_id),
                    cargo_id=str(cargo_id),
                    pickup_time=pickup_time.isoformat(),
                    delivery_time=delivery_time.isoformat())

        # Validate times
        if delivery_time <= pickup_time:
            return False, "Delivery time must be after pickup time"

        # Validate minimum duration (e.g., 30 minutes)
        min_duration = timedelta(minutes=30)
        if delivery_time - pickup_time < min_duration:
            return False, f"Route duration must be at least {min_duration}"

        # For PoC, we assume transport and cargo exist and are valid
        # In production, we would do more thorough validation here
        return True, None

    def validate_route_feasibility(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if a route is feasible based on provided data.
        
        Args:
            route_data: Dictionary containing route details
            
        Returns:
            Dictionary with validation results
        """
        logger.debug("Checking route feasibility", route_data=route_data)

        validation_details = {
            "transport_valid": True,
            "cargo_valid": True,
            "timeline_valid": True,
            "distance_valid": True,
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }

        # For PoC, we return all validations as true
        # In production, we would implement actual validation logic
        return validation_details

    def validate_timeline_events(
        self,
        events: List[Dict[str, Any]],
        route_id: Optional[UUID] = None
    ) -> Tuple[bool, Optional[str], Optional[List[TimelineEvent]]]:
        """
        Validate timeline events for a route.
        
        Args:
            events: List of event dictionaries to validate
            route_id: Optional route ID for existing route
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str], validated_events: Optional[List[TimelineEvent]])
        """
        logger.debug("Validating timeline events",
                    event_count=len(events),
                    route_id=str(route_id) if route_id else None)

        try:
            validated_events = []
            last_time = None
            
            for event_data in events:
                # Validate location exists
                location_id = UUID(event_data["location_id"])
                location = self._location_repo.find_by_id(location_id)
                if not location:
                    return False, f"Location not found: {location_id}", None

                # Parse and validate time
                planned_time = datetime.fromisoformat(event_data["planned_time"].replace("Z", "+00:00"))
                if last_time and planned_time <= last_time:
                    return False, "Events must be in chronological order", None
                last_time = planned_time

                # Validate duration
                duration_hours = float(event_data["duration_hours"])
                if duration_hours <= 0:
                    return False, "Duration must be positive", None

                # Create validated event
                event = TimelineEvent(
                    id=uuid4(),
                    route_id=route_id or uuid4(),  # Temporary ID if route doesn't exist yet
                    type=event_data["type"],
                    location_id=location_id,
                    planned_time=planned_time,
                    duration_hours=duration_hours,
                    event_order=event_data["event_order"],
                    status=EventStatus.PENDING
                )
                validated_events.append(event)

            return True, None, validated_events

        except (ValueError, KeyError) as e:
            return False, f"Invalid event data: {str(e)}", None
        except Exception as e:
            logger.error("Error validating timeline events", error=str(e))
            return False, "Internal validation error", None

    def update_route_status(
        self,
        route_id: UUID,
        new_status: str,
        comment: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Route]]:
        """
        Update route status with validation and history tracking.
        
        Args:
            route_id: ID of the route to update
            new_status: New status to set
            comment: Optional comment about the status change
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str], updated_route: Optional[Route])
        """
        logger.debug("Updating route status",
                    route_id=str(route_id),
                    new_status=new_status,
                    comment=comment)

        try:
            # Get route
            route = self._route_repo.find_by_id(route_id)
            if not route:
                return False, "Route not found", None

            # Validate status transition
            if not self._is_valid_status_transition(route.status, new_status):
                return False, f"Invalid status transition: {route.status} -> {new_status}", None

            # Update status
            old_status = route.status
            route.status = RouteStatus(new_status)
            
            # Update timeline events based on new status
            if new_status == "IN_PROGRESS":
                self._update_timeline_events_for_transit(route)
            elif new_status == "COMPLETED":
                self._update_timeline_events_for_completion(route)
            elif new_status == "CANCELLED":
                self._update_timeline_events_for_cancellation(route)

            # Create status history entry
            from datetime import datetime, timezone
            from uuid import uuid4
            from backend.infrastructure.models.route_models import RouteStatusHistoryModel

            history_entry = RouteStatusHistoryModel(
                id=str(uuid4()),
                route_id=str(route_id),
                status=new_status,
                timestamp=datetime.now(timezone.utc),
                comment=comment
            )
            self._route_repo._db.add(history_entry)

            # Save updated route
            updated_route = self._route_repo.save(route)
            
            # Log status change
            logger.info("Route status updated",
                       route_id=str(route_id),
                       old_status=old_status,
                       new_status=new_status,
                       comment=comment)

            return True, None, updated_route

        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            logger.error("Error updating route status", error=str(e))
            return False, "Internal error updating status", None

    def _is_valid_status_transition(self, current_status: RouteStatus, new_status: str) -> bool:
        """Check if a status transition is valid."""
        # Define valid transitions
        valid_transitions = {
            RouteStatus.DRAFT: ["PLANNED", "CANCELLED"],
            RouteStatus.PLANNED: ["IN_PROGRESS", "CANCELLED"],
            RouteStatus.IN_PROGRESS: ["COMPLETED", "CANCELLED"],
            RouteStatus.COMPLETED: [],  # Terminal state
            RouteStatus.CANCELLED: []   # Terminal state
        }

        return new_status in valid_transitions.get(current_status, []) 

    def get_segment_route_points(self, segment_id: UUID) -> List[List[float]]:
        """Get route points for a segment."""
        try:
            # Get segment from repository
            segment = self._route_repo.find_segment_by_id(segment_id)
            if not segment:
                return []

            # Get start and end locations
            start_location = self._location_repo.find_by_id(segment.start_location_id)
            end_location = self._location_repo.find_by_id(segment.end_location_id)
            if not start_location or not end_location:
                return []

            # Calculate route points using Google Maps
            _, _, _, route_points = self._route_calculator.calculate_route(
                start_location, end_location
            )
            return route_points

        except Exception as e:
            logger.error(f"Failed to get route points for segment {segment_id}: {str(e)}")
            return [] 