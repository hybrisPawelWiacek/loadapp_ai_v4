"""Cost service for managing cost-related business logic."""
from decimal import Decimal
from typing import Dict, Optional, Protocol
from uuid import UUID, uuid4

from ..entities.cargo import CostSettings, CostBreakdown
from ..entities.route import Route, CountrySegment, EmptyDriving
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


class EmptyDrivingRepository(Protocol):
    """Repository interface for EmptyDriving entity."""
    def find_by_id(self, id: UUID) -> Optional[EmptyDriving]:
        """Find empty driving by ID."""
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
        empty_driving_repo: EmptyDrivingRepository,
        toll_calculator: TollCalculationPort
    ):
        self._settings_repo = settings_repo
        self._breakdown_repo = breakdown_repo
        self._empty_driving_repo = empty_driving_repo
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
            id=uuid4(),
            route_id=route_id,
            enabled_components=enabled_components,
            rates=rates,
            business_entity_id=business_entity_id
        )
        return self._settings_repo.save(settings)

    def clone_cost_settings(
        self,
        source_route_id: UUID,
        target_route_id: UUID,
        rate_modifications: Optional[Dict[str, Decimal]] = None
    ) -> CostSettings:
        """Clone cost settings from one route to another with optional rate modifications.
        
        Args:
            source_route_id: UUID of the route to clone settings from
            target_route_id: UUID of the route to clone settings to
            rate_modifications: Optional dictionary of rate modifications to apply
        
        Returns:
            New CostSettings instance for target route
            
        Raises:
            ValueError: If source settings not found or rates are invalid
        """
        # Get source settings
        source_settings = self._settings_repo.find_by_route_id(source_route_id)
        if not source_settings:
            raise ValueError("Source route cost settings not found")
            
        # Create new rates dictionary
        new_rates = source_settings.rates.copy()
        
        # Apply rate modifications if provided
        if rate_modifications:
            for rate_key, new_rate in rate_modifications.items():
                if not isinstance(new_rate, Decimal):
                    new_rate = Decimal(str(new_rate))
                new_rates[rate_key] = new_rate
                
        # Create new settings for target route
        return self.create_cost_settings(
            route_id=target_route_id,
            business_entity_id=source_settings.business_entity_id,
            enabled_components=source_settings.enabled_components.copy(),
            rates=new_rates
        )

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

        # Load empty driving record
        empty_driving = self._empty_driving_repo.find_by_id(route.empty_driving_id)
        if not empty_driving:
            raise ValueError("Empty driving record not found for route")

        # Calculate fuel costs per country
        fuel_costs = self._calculate_fuel_costs(route, transport, settings, empty_driving)

        # Calculate toll costs per country
        toll_costs = self._calculate_toll_costs(route, transport, settings)

        # Calculate driver costs
        driver_costs = self._calculate_driver_costs(route, transport, settings)

        # Calculate overhead costs
        overhead_costs = self._calculate_overhead_costs(business, settings)

        # Calculate timeline event costs
        timeline_event_costs = self._calculate_event_costs(route, settings)

        # Calculate total cost
        total_cost = (
            sum(fuel_costs.values()) +
            sum(toll_costs.values()) +
            driver_costs +
            overhead_costs +
            sum(timeline_event_costs.values())
        )

        # Create and save cost breakdown
        breakdown = CostBreakdown(
            id=uuid4(),
            route_id=route.id,
            fuel_costs=fuel_costs,
            toll_costs=toll_costs,
            driver_costs=driver_costs,
            overhead_costs=overhead_costs,
            timeline_event_costs=timeline_event_costs,
            total_cost=total_cost
        )
        return self._breakdown_repo.save(breakdown)

    def _calculate_fuel_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings,
        empty_driving: EmptyDriving
    ) -> Dict[str, Decimal]:
        """Calculate fuel costs per country segment."""
        if "fuel" not in settings.enabled_components:
            return {segment.country_code: Decimal("0")
                   for segment in route.country_segments}

        fuel_rate = settings.rates.get("fuel_rate", Decimal("1.5"))  # Default rate
        costs = {}

        # First, calculate costs for main route segments
        for segment in route.country_segments:
            # Calculate based on loaded consumption
            consumption = (
                transport.truck_specs.fuel_consumption_loaded *
                segment.distance_km
            )
            costs[segment.country_code] = Decimal(str(consumption)) * fuel_rate

        # Then add empty driving cost to first country
        if route.country_segments:
            first_country = route.country_segments[0].country_code
            empty_consumption = (
                transport.truck_specs.fuel_consumption_empty *
                empty_driving.distance_km
            )
            costs[first_country] = costs.get(first_country, Decimal("0")) + (Decimal(str(empty_consumption)) * fuel_rate)

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

    def calculate_cost_breakdown(self, route: Route, transport: Transport) -> CostBreakdown:
        """Calculate the cost breakdown for a route with a given transport."""
        # Initialize empty dictionaries for costs
        timeline_event_costs = {}
        total_cost = Decimal('0.0')

        # Calculate costs for each timeline event
        for event in route.timeline_events:
            event_cost = self._calculate_event_cost(event, transport)
            timeline_event_costs[event.type] = event_cost
            total_cost += event_cost

        # Add empty driving costs if applicable
        if route.empty_driving:
            empty_driving_cost = self._calculate_empty_driving_cost(route.empty_driving, transport)
            timeline_event_costs['empty_driving'] = empty_driving_cost
            total_cost += empty_driving_cost

        return CostBreakdown(
            id=uuid4(),
            route_id=route.id,
            timeline_event_costs=timeline_event_costs,
            total_cost=total_cost
        ) 