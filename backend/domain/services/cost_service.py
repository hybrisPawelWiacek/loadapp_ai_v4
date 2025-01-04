"""Cost service for managing cost-related business logic."""
from decimal import Decimal
from typing import Dict, Optional, Protocol, List, Tuple, Any
from uuid import UUID, uuid4

from ..entities.cargo import CostSettings, CostSettingsCreate, CostBreakdown
from ..entities.route import Route, CountrySegment, EmptyDriving
from ..entities.transport import Transport
from ..entities.business import BusinessEntity
from ..entities.rate_types import RateType, validate_rate
from ...infrastructure.repositories.rate_validation_repository import RateValidationRepository


class CostSettingsRepository(Protocol):
    """Repository interface for CostSettings entity."""
    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings."""
        ...

    def find_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Find cost settings by route ID."""
        ...

    def create_settings(
        self,
        route_id: UUID,
        settings: CostSettingsCreate,
        business_entity_id: UUID
    ) -> CostSettings:
        """Create new cost settings."""
        ...

    def update_settings(
        self,
        route_id: UUID,
        updates: Dict[str, Any]
    ) -> CostSettings:
        """Update existing cost settings."""
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
        truck_specs: dict,
        business_entity_id: Optional[UUID] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate toll costs for a country segment.
        
        Args:
            segment: Route segment in a specific country
            truck_specs: Dictionary containing truck specifications
                - toll_class: Toll class of the truck
                - euro_class: Euro emission class
                - co2_class: CO2 emission class
            business_entity_id: Optional business entity ID for rate overrides
            overrides: Optional dictionary with rate override settings
                - vehicle_class: Vehicle class for override lookup
                - route_type: Optional route type for specific rates
                
        Returns:
            Decimal representing toll costs for the segment
        """
        ...


class CostService:
    """Service for managing cost-related business logic."""

    def __init__(
        self,
        settings_repo: CostSettingsRepository,
        breakdown_repo: CostBreakdownRepository,
        empty_driving_repo: EmptyDrivingRepository,
        toll_calculator: TollCalculationPort,
        rate_validation_repo: RateValidationRepository
    ):
        self._settings_repo = settings_repo
        self._breakdown_repo = breakdown_repo
        self._empty_driving_repo = empty_driving_repo
        self._toll_calculator = toll_calculator
        self._rate_validation_repo = rate_validation_repo

    def validate_rates(self, rates: Dict[str, Decimal]) -> Tuple[bool, List[str]]:
        """
        Validate rates against their schemas.
        
        Args:
            rates: Dictionary of rates to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        schemas = self._rate_validation_repo.get_all_schemas()
        
        for rate_key, value in rates.items():
            try:
                rate_type = RateType(rate_key)
                schema = schemas.get(rate_type)
                
                if not schema:
                    errors.append(f"No validation schema found for rate type: {rate_key}")
                    continue
                    
                if not validate_rate(rate_type, value, schema):
                    errors.append(
                        f"Rate {rate_key} value {value} outside allowed range "
                        f"({schema.min_value} - {schema.max_value})"
                    )
                    
            except ValueError:
                errors.append(f"Unknown rate type: {rate_key}")
                
        return len(errors) == 0, errors

    def create_cost_settings(
        self,
        route_id: UUID,
        settings: CostSettingsCreate,
        business_entity_id: UUID
    ) -> CostSettings:
        """
        Create cost settings with rate validation.
        
        Args:
            route_id: ID of the route to create settings for
            settings: Settings to create
            business_entity_id: ID of the business entity
            
        Returns:
            Created cost settings
            
        Raises:
            ValueError: If rates are invalid
        """
        print(f"[DEBUG] Creating cost settings for route_id: {route_id}, business_entity_id: {business_entity_id}")
        print(f"[DEBUG] Settings input: {settings}")
        
        is_valid, errors = self.validate_rates(settings.rates)
        print(f"[DEBUG] Rate validation result - is_valid: {is_valid}, errors: {errors}")
        
        if not is_valid:
            error_msg = f"Invalid rates: {'; '.join(errors)}"
            print(f"[DEBUG] Validation failed: {error_msg}")
            raise ValueError(error_msg)
            
        try:
            result = self._settings_repo.create_settings(
                route_id=route_id,
                settings=settings,
                business_entity_id=business_entity_id
            )
            print(f"[DEBUG] Successfully created settings: {result}")
            return result
        except Exception as e:
            print(f"[DEBUG] Error creating settings in repository: {str(e)}")
            raise

    def clone_cost_settings(
        self,
        source_route_id: UUID,
        target_route_id: UUID,
        rate_modifications: Optional[Dict[str, Decimal]] = None
    ) -> CostSettings:
        """
        Clone cost settings with rate validation for modifications.
        
        Args:
            source_route_id: ID of route to clone settings from
            target_route_id: ID of route to clone settings to
            rate_modifications: Optional modifications to rates
            
        Returns:
            New cost settings for target route
            
        Raises:
            ValueError: If source settings not found or rates are invalid
        """
        source_settings = self._settings_repo.find_by_route_id(source_route_id)
        if not source_settings:
            raise ValueError("Source route cost settings not found")
            
        new_rates = source_settings.rates.copy()
        
        if rate_modifications:
            # Validate rate modifications
            is_valid, errors = self.validate_rates(rate_modifications)
            if not is_valid:
                raise ValueError(f"Invalid rate modifications: {'; '.join(errors)}")
                
            new_rates.update(rate_modifications)
            
        # Create new settings with validated rates
        return self._settings_repo.create_settings(
            target_route_id,
            CostSettingsCreate(
                enabled_components=source_settings.enabled_components,
                rates=new_rates
            ),
            source_settings.business_entity_id
        )

    def update_cost_settings_partial(
        self,
        route_id: UUID,
        updates: Dict[str, Any]
    ) -> CostSettings:
        """
        Partially update cost settings for a route.
        
        Args:
            route_id: ID of the route to update settings for
            updates: Dictionary containing fields to update
                - enabled_components: Optional[List[str]]
                - rates: Optional[Dict[str, Decimal]]
                
        Returns:
            Updated cost settings
            
        Raises:
            ValueError: If settings not found or updates are invalid
            ValueError: If rate values are invalid
        """
        # Get existing settings
        settings = self._settings_repo.find_by_route_id(route_id)
        if not settings:
            raise ValueError("Cost settings not found for route")

        # Handle rate updates if present
        if "rates" in updates and updates["rates"]:
            # Validate new rates
            is_valid, errors = self.validate_rates(updates["rates"])
            if not is_valid:
                raise ValueError(f"Invalid rates in update: {'; '.join(errors)}")
            
            # Update rates
            new_rates = settings.rates.copy()
            new_rates.update(updates["rates"])
            updates["rates"] = new_rates

        # Handle enabled components update if present
        if "enabled_components" in updates:
            # Ensure at least one component is enabled
            if not updates["enabled_components"]:
                raise ValueError("At least one component must be enabled")

        # Update and save settings
        return self._settings_repo.update_settings(
            route_id=route_id,
            updates=updates
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
        toll_costs = self._calculate_toll_costs(route, transport, settings, business)

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
        settings: CostSettings,
        business: Optional[BusinessEntity] = None
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

        # Prepare overrides if business entity is provided
        overrides = None
        if business:
            overrides = {
                "vehicle_class": transport.truck_specs.toll_class,
                "route_type": getattr(route, "route_type", None)
            }

        for segment in route.country_segments:
            costs[segment.country_code] = self._toll_calculator.calculate_toll(
                segment,
                truck_specs,
                business.id if business else None,
                overrides
            )

        return costs

    def _calculate_driver_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """
        Calculate detailed driver costs for the route.
        
        Args:
            route: Route to calculate costs for
            transport: Transport with driver specifications
            settings: Cost settings with enabled components
            
        Returns:
            Dictionary containing breakdown of driver costs
        """
        if "driver" not in settings.enabled_components:
            return {
                "base_cost": Decimal("0"),
                "regular_hours_cost": Decimal("0"),
                "overtime_cost": Decimal("0"),
                "total_cost": Decimal("0")
            }

        # Calculate days (round up partial days)
        total_hours = route.total_duration_hours
        days = (int(total_hours) + 23) // 24

        # Calculate base cost
        base_cost = transport.driver_specs.daily_rate * Decimal(str(days))

        # Calculate regular and overtime hours
        max_regular_hours = transport.driver_specs.max_driving_hours * days
        regular_hours = min(float(total_hours), float(max_regular_hours))
        overtime_hours = max(0, float(total_hours) - regular_hours)

        # Calculate time-based costs
        regular_hours_cost = (
            Decimal(str(regular_hours)) * 
            transport.driver_specs.driving_time_rate
        )
        
        overtime_cost = (
            Decimal(str(overtime_hours)) * 
            transport.driver_specs.driving_time_rate * 
            transport.driver_specs.overtime_rate_multiplier
        )

        # Calculate total cost
        total_cost = base_cost + regular_hours_cost + overtime_cost

        return {
            "base_cost": base_cost,
            "regular_hours_cost": regular_hours_cost,
            "overtime_cost": overtime_cost,
            "total_cost": total_cost
        }

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