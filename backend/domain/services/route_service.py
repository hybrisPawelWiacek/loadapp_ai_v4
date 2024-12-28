"""Route service for managing route-related business logic."""
from datetime import datetime, timedelta
from typing import List, Optional, Protocol
from uuid import UUID, uuid4

from ..entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving
)


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
        route_calculator: RouteCalculationPort
    ):
        self._route_repo = route_repo
        self._route_calculator = route_calculator

    def create_route(
        self,
        transport_id: UUID,
        business_entity_id: UUID,
        cargo_id: UUID,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> Route:
        """Create a new route with timeline events."""
        # Calculate main route
        distance, duration, segments = self._route_calculator.calculate_route(
            origin, destination
        )

        # Create empty driving
        empty_driving = EmptyDriving()  # Uses default 200km/4h

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
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            empty_driving=empty_driving,
            timeline_events=timeline_events,
            country_segments=segments,
            total_distance_km=distance + empty_driving.distance_km,
            total_duration_hours=duration + empty_driving.duration_hours,
            is_feasible=True  # Always true for PoC
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