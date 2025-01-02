"""Route service for managing route-related business logic."""
from datetime import datetime, timedelta
from typing import List, Optional, Protocol
from uuid import UUID, uuid4

from ..entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving, RouteStatus
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
        """Create a new route with timeline events."""
        # Get locations
        origin = self._location_repo.find_by_id(origin_id)
        if not origin:
            raise ValueError(f"Origin location not found: {origin_id}")
        
        destination = self._location_repo.find_by_id(destination_id)
        if not destination:
            raise ValueError(f"Destination location not found: {destination_id}")

        # Calculate main route
        distance, duration, segments = self._route_calculator.calculate_route(
            origin, destination
        )

        # Create empty driving
        empty_driving_id = uuid4()
        empty_driving = EmptyDriving(
            id=empty_driving_id,
            distance_km=200.0,  # Default value
            duration_hours=4.0  # Default value
        )

        # Create timeline events
        timeline_events = self._generate_timeline_events(
            origin, destination, pickup_time, delivery_time
        )

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
            empty_driving_id=empty_driving_id,
            timeline_events=timeline_events,
            country_segments=segments,
            total_distance_km=float(distance + empty_driving.distance_km),
            total_duration_hours=float(duration + empty_driving.duration_hours),
            is_feasible=True,  # Always true for PoC
            status=RouteStatus.DRAFT
        )

        return self._route_repo.save(route)

    def _generate_timeline_events(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> List[TimelineEvent]:
        """Generate timeline events for the route."""
        total_duration = delivery_time - pickup_time
        mid_point = pickup_time + (total_duration / 2)

        events = [
            # Pickup event
            TimelineEvent(
                id=uuid4(),
                type="pickup",
                location=origin,
                planned_time=pickup_time,
                duration_hours=1.0,
                event_order=1
            ),
            # Rest event in middle
            TimelineEvent(
                id=uuid4(),
                type="rest",
                location=origin,  # Simplified for PoC
                planned_time=mid_point,
                duration_hours=1.0,
                event_order=2
            ),
            # Delivery event
            TimelineEvent(
                id=uuid4(),
                type="delivery",
                location=destination,
                planned_time=delivery_time,
                duration_hours=1.0,
                event_order=3
            )
        ]

        return events

    def get_route(self, route_id: UUID) -> Optional[Route]:
        """Retrieve a route by ID."""
        return self._route_repo.find_by_id(route_id)

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
        # Find route by cargo ID
        routes = self._route_repo.find_by_cargo_id(cargo_id)
        if not routes:
            return
            
        # Update route status based on cargo status
        for route in routes:
            if new_status == "in_transit":
                route.status = "active"
                self._route_repo.save(route) 