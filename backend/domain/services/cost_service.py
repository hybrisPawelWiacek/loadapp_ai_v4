"""Cost service for managing cost-related business logic."""
from decimal import Decimal
from typing import Dict, Optional, Protocol
from uuid import UUID

from ..entities.cargo import CostSettings, CostBreakdown
from ..entities.route import Route, CountrySegment
from ..entities.transport import Transport
from ..entities.business import BusinessEntity


class CostSettingsRepository(Protocol):
    """Repository interface for CostSettings entity."""
    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings."""
        ...

    def find_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Find cost settings by route ID."""
        ...


class CostBreakdownRepository(Protocol):
    """Repository interface for CostBreakdown entity."""
    def save(self, breakdown: CostBreakdown) -> CostBreakdown:
        """Save cost breakdown."""
        ...

    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find cost breakdown by route ID."""
        ...


class TollCalculationPort(Protocol):
    """External service port for toll calculations."""
    def calculate_toll(
        self,
        segment: CountrySegment,
        truck_specs: dict
    ) -> Decimal:
        """Calculate toll costs for a country segment."""
        ...


class CostService:
    """Service for managing cost-related business logic."""

    def __init__(
        self,
        settings_repo: CostSettingsRepository,
        breakdown_repo: CostBreakdownRepository,
        toll_calculator: TollCalculationPort
    ):
        self._settings_repo = settings_repo
        self._breakdown_repo = breakdown_repo
        self._toll_calculator = toll_calculator

    def create_cost_settings(
        self,
        route_id: UUID,
        business_entity_id: UUID,
        enabled_components: list[str],
        rates: Dict[str, Decimal]
    ) -> CostSettings:
        """Create new cost settings for a route."""
        settings = CostSettings(
            id=UUID(),
            route_id=route_id,
            enabled_components=enabled_components,
            rates=rates,
            business_entity_id=business_entity_id
        )
        return self._settings_repo.save(settings)

    def calculate_costs(
        self,
        route: Route,
        transport: Transport,
        business: BusinessEntity
    ) -> CostBreakdown:
        """Calculate complete cost breakdown for a route."""
        settings = self._settings_repo.find_by_route_id(route.id)
        if not settings:
            raise ValueError("Cost settings not found for route")

        # Calculate fuel costs per country
        fuel_costs = self._calculate_fuel_costs(route, transport, settings)

        # Calculate toll costs per country
        toll_costs = self._calculate_toll_costs(route, transport, settings)

        # Calculate driver costs
        driver_costs = self._calculate_driver_costs(route, transport, settings)

        # Calculate overhead costs
        overhead_costs = self._calculate_overhead_costs(business, settings)

        # Calculate timeline event costs
        event_costs = self._calculate_event_costs(route, settings)

        # Calculate total
        total_cost = (
            sum(fuel_costs.values()) +
            sum(toll_costs.values()) +
            driver_costs +
            overhead_costs +
            sum(event_costs.values())
        )

        # Create and save breakdown
        breakdown = CostBreakdown(
            route_id=route.id,
            fuel_costs=fuel_costs,
            toll_costs=toll_costs,
            driver_costs=driver_costs,
            overhead_costs=overhead_costs,
            timeline_event_costs=event_costs,
            total_cost=total_cost
        )

        return self._breakdown_repo.save(breakdown)

    def _calculate_fuel_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """Calculate fuel costs per country segment."""
        if "fuel" not in settings.enabled_components:
            return {segment.country_code: Decimal("0")
                   for segment in route.country_segments}

        fuel_rate = settings.rates.get("fuel_rate", Decimal("1.5"))  # Default rate
        costs = {}

        for segment in route.country_segments:
            # Calculate based on loaded consumption
            consumption = (
                transport.truck_specs.fuel_consumption_loaded *
                segment.distance_km
            )
            costs[segment.country_code] = Decimal(str(consumption)) * fuel_rate

        # Add empty driving fuel cost to first country
        if route.country_segments:
            first_country = route.country_segments[0].country_code
            empty_consumption = (
                transport.truck_specs.fuel_consumption_empty *
                route.empty_driving.distance_km
            )
            costs[first_country] += Decimal(str(empty_consumption)) * fuel_rate

        return costs

    def _calculate_toll_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """Calculate toll costs per country segment."""
        if "toll" not in settings.enabled_components:
            return {segment.country_code: Decimal("0")
                   for segment in route.country_segments}

        costs = {}
        truck_specs = {
            "toll_class": transport.truck_specs.toll_class,
            "euro_class": transport.truck_specs.euro_class,
            "co2_class": transport.truck_specs.co2_class
        }

        for segment in route.country_segments:
            costs[segment.country_code] = self._toll_calculator.calculate_toll(
                segment, truck_specs
            )

        return costs

    def _calculate_driver_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings
    ) -> Decimal:
        """Calculate driver costs for the route."""
        if "driver" not in settings.enabled_components:
            return Decimal("0")

        # Calculate days (round up partial days)
        total_hours = route.total_duration_hours
        days = (int(total_hours) + 23) // 24

        return transport.driver_specs.daily_rate * Decimal(str(days))

    def _calculate_overhead_costs(
        self,
        business: BusinessEntity,
        settings: CostSettings
    ) -> Decimal:
        """Calculate business overhead costs."""
        if "overhead" not in settings.enabled_components:
            return Decimal("0")

        # Sum all overhead costs
        return sum(business.cost_overheads.values())

    def _calculate_event_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """Calculate costs for timeline events."""
        if "events" not in settings.enabled_components:
            return {event.type: Decimal("0") for event in route.timeline_events}

        event_rate = settings.rates.get("event_rate", Decimal("50"))  # Default rate
        return {
            event.type: event_rate * Decimal(str(event.duration_hours))
            for event in route.timeline_events
        } 