"""Cost service for managing cost-related business logic."""
from decimal import Decimal
from typing import Dict, Optional, Protocol, List, Tuple, Any
from uuid import UUID, uuid4
import decimal
import logging

from ..entities.cargo import CostSettings, CostSettingsCreate, CostBreakdown
from ..entities.route import Route, CountrySegment, EmptyDriving
from ..entities.transport import Transport
from ..entities.business import BusinessEntity
from ..entities.rate_types import RateType, validate_rate
from ...infrastructure.repositories.rate_validation_repository import RateValidationRepository
from ...infrastructure.data.fuel_rates import get_fuel_rate


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


class RouteRepository(Protocol):
    """Repository interface for Route entity."""
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find route by ID."""
        ...


class TransportRepository(Protocol):
    """Repository interface for Transport entity."""
    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find transport by ID."""
        ...


class BusinessRepository(Protocol):
    """Repository interface for Business entity."""
    def find_by_id(self, id: UUID) -> Optional[BusinessEntity]:
        """Find business entity by ID."""
        ...


class CostService:
    """Service for managing cost-related business logic."""

    def __init__(
        self,
        settings_repo: CostSettingsRepository,
        breakdown_repo: CostBreakdownRepository,
        empty_driving_repo: EmptyDrivingRepository,
        toll_calculator: TollCalculationPort,
        rate_validation_repo: RateValidationRepository,
        route_repo: RouteRepository,
        transport_repo: TransportRepository,
        business_repo: BusinessRepository
    ):
        self._settings_repo = settings_repo
        self._breakdown_repo = breakdown_repo
        self._empty_driving_repo = empty_driving_repo
        self._toll_calculator = toll_calculator
        self._rate_validation_repo = rate_validation_repo
        self._route_repo = route_repo
        self._transport_repo = transport_repo
        self._business_repo = business_repo
        self._logger = logging.getLogger(__name__)

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
        
        # Get route to access country segments
        route = self._route_repo.find_by_id(route_id)
        if not route:
            raise ValueError(f"Route not found: {route_id}")
        
        # Apply default rates based on enabled components
        rates = {}
        for rate_key, rate_value in settings.rates.items():
            # Ensure rate values are properly formatted decimals
            try:
                if isinstance(rate_value, str):
                    rates[rate_key] = Decimal(rate_value)
                elif isinstance(rate_value, (int, float)):
                    rates[rate_key] = Decimal(str(rate_value))
                elif isinstance(rate_value, Decimal):
                    rates[rate_key] = rate_value
                else:
                    raise ValueError(f"Invalid rate value type for {rate_key}: {type(rate_value)}")
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                raise ValueError(f"Invalid rate value for {rate_key}: {rate_value}") from e

        if "fuel" in settings.enabled_components:
            # Get default fuel rates for each country in the route
            for segment in route.country_segments:
                country_code = segment.country_code
                if "fuel_rate" not in rates:
                    rates["fuel_rate"] = Decimal(str(get_fuel_rate(country_code)))
        
        if "toll" in settings.enabled_components:
            # Get default toll rate multiplier if not provided
            if "toll_rate_multiplier" not in rates:
                rates["toll_rate_multiplier"] = Decimal("1.0")  # Default multiplier
        
        if "driver" in settings.enabled_components:
            # Get transport to access driver specifications
            transport = self._transport_repo.find_by_id(route.transport_id)
            if transport:
                if "driver_base_rate" not in rates:
                    rates["driver_base_rate"] = Decimal(str(transport.driver_specs.daily_rate))
                if "driver_time_rate" not in rates:
                    rates["driver_time_rate"] = Decimal(str(transport.driver_specs.driving_time_rate))
        
        if "events" in settings.enabled_components and "event_rate" not in rates:
            rates["event_rate"] = Decimal("50.0")  # Default event rate

        if "overhead" in settings.enabled_components:
            # Get business entity to access overhead costs
            business = self._business_repo.find_by_id(business_entity_id)
            if not business:
                raise ValueError(f"Business entity not found: {business_entity_id}")
            # Add overhead rates from business entity
            for key, value in business.cost_overheads.items():
                rate_key = f"overhead_{key}_rate"
                if rate_key not in rates:
                    try:
                        # Convert the value to Decimal if it's not already
                        if isinstance(value, str):
                            rates[rate_key] = Decimal(value)
                        elif isinstance(value, (int, float)):
                            rates[rate_key] = Decimal(str(value))
                        elif isinstance(value, Decimal):
                            rates[rate_key] = value
                        else:
                            raise ValueError(f"Invalid overhead cost value type for {key}: {type(value)}")
                    except (ValueError, TypeError, decimal.InvalidOperation) as e:
                        raise ValueError(f"Invalid overhead cost value for {key}: {value}") from e
        
        # Update settings with default rates
        settings.rates = rates
        
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
            ValueError: If rates are invalid
        """
        print(f"[DEBUG] Updating cost settings for route_id: {route_id}")
        print(f"[DEBUG] Updates: {updates}")
        
        if "rates" in updates:
            # Convert rate values to Decimal
            rates = {}
            for rate_key, rate_value in updates["rates"].items():
                try:
                    if isinstance(rate_value, str):
                        rates[rate_key] = Decimal(rate_value)
                    elif isinstance(rate_value, (int, float)):
                        rates[rate_key] = Decimal(str(rate_value))
                    elif isinstance(rate_value, Decimal):
                        rates[rate_key] = rate_value
                    else:
                        raise ValueError(f"Invalid rate value type for {rate_key}: {type(rate_value)}")
                except (ValueError, TypeError, decimal.InvalidOperation) as e:
                    raise ValueError(f"Invalid rate value for {rate_key}: {rate_value}") from e
            
            # Validate updated rates
            is_valid, errors = self.validate_rates(rates)
            if not is_valid:
                raise ValueError(f"Invalid rates: {'; '.join(errors)}")
            
            updates["rates"] = rates
        
        try:
            result = self._settings_repo.update_settings(route_id, updates)
            print(f"[DEBUG] Successfully updated settings: {result}")
            return result
        except Exception as e:
            print(f"[DEBUG] Error updating settings in repository: {str(e)}")
            raise

    def calculate_costs(
        self,
        route: Route,
        transport: Transport,
        business: BusinessEntity
    ) -> CostBreakdown:
        """Calculate complete cost breakdown for a route."""
        try:
            # Validate business entity operates in all route countries
            route_countries = {segment.country_code for segment in route.country_segments}
            business_countries = set(business.operating_countries)
            if not route_countries.issubset(business_countries):
                missing_countries = route_countries - business_countries
                self._logger.error(
                    f"Business entity {business.id} does not operate in required countries: {list(missing_countries)}"
                )
                raise ValueError(f"Business entity does not operate in required countries: {missing_countries}")

            # Load cost settings
            settings = self._settings_repo.find_by_route_id(route.id)
            if not settings:
                self._logger.error(f"Cost settings not found for route {route.id}")
                raise ValueError("Cost settings not found for route")

            # Load empty driving record
            empty_driving = self._empty_driving_repo.find_by_id(route.empty_driving_id)
            if not empty_driving:
                self._logger.error(
                    f"Empty driving record not found for route {route.id}, empty_driving_id: {route.empty_driving_id}"
                )
                raise ValueError("Empty driving record not found for route")

            # Calculate fuel costs per country
            try:
                fuel_costs = self._calculate_fuel_costs(route, transport, settings, empty_driving)
                self._logger.info(f"Calculated fuel costs for route {route.id}: {fuel_costs}")
            except Exception as e:
                self._logger.error(f"Error calculating fuel costs for route {route.id}: {str(e)}")
                raise

            # Calculate toll costs per country
            try:
                toll_costs = self._calculate_toll_costs(route, transport, settings, business)
                self._logger.info(f"Calculated toll costs for route {route.id}: {toll_costs}")
            except Exception as e:
                self._logger.error(f"Error calculating toll costs for route {route.id}: {str(e)}")
                raise

            # Calculate driver costs
            try:
                driver_costs = self._calculate_driver_costs(route, transport, settings)
                self._logger.info(f"Calculated driver costs for route {route.id}: {driver_costs}")
            except Exception as e:
                self._logger.error(f"Error calculating driver costs for route {route.id}: {str(e)}")
                raise

            # Calculate overhead costs
            try:
                overhead_costs = self._calculate_overhead_costs(business, settings)
                self._logger.info(f"Calculated overhead costs for route {route.id}: {overhead_costs}")
            except Exception as e:
                self._logger.error(f"Error calculating overhead costs for route {route.id}: {str(e)}")
                raise

            # Calculate timeline event costs
            try:
                timeline_event_costs = self._calculate_event_costs(route, settings)
                self._logger.info(f"Calculated timeline event costs for route {route.id}: {timeline_event_costs}")
            except Exception as e:
                self._logger.error(f"Error calculating timeline event costs for route {route.id}: {str(e)}")
                raise

            # Calculate total cost
            try:
                total_cost = (
                    sum(Decimal(str(value)) for value in fuel_costs.values()) +
                    sum(Decimal(str(value[0])) if isinstance(value, tuple) else Decimal(str(value)) for value in toll_costs.values()) +
                    driver_costs["total_cost"] +
                    overhead_costs +
                    sum(Decimal(str(value)) for value in timeline_event_costs.values())
                )
                self._logger.info(f"Calculated total cost for route {route.id}: {total_cost}")
            except Exception as e:
                self._logger.error(f"Error calculating total cost for route {route.id}: {str(e)}")
                raise

            # Create and return cost breakdown
            return CostBreakdown(
                id=uuid4(),
                route_id=route.id,
                fuel_costs=fuel_costs,
                toll_costs={
                    country: value[0] if isinstance(value, tuple) else value
                    for country, value in toll_costs.items()
                },
                driver_costs=driver_costs,
                overhead_costs=overhead_costs,
                timeline_event_costs=timeline_event_costs,
                total_cost=total_cost
            )

        except Exception as e:
            self._logger.error(
                f"Error in calculate_costs for route {route.id}, transport {transport.id}, business {business.id}: {str(e)} ({type(e).__name__})"
            )
            raise

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
            consumption = Decimal(str(transport.truck_specs.fuel_consumption_loaded)) * Decimal(str(segment.distance_km))
            costs[segment.country_code] = consumption * fuel_rate

        # Then add empty driving cost to first country
        if route.country_segments and empty_driving:
            first_country = route.country_segments[0].country_code
            empty_consumption = Decimal(str(transport.truck_specs.fuel_consumption_empty)) * Decimal(str(empty_driving.distance_km))
            costs[first_country] = costs.get(first_country, Decimal("0")) + (empty_consumption * fuel_rate)

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
            toll_cost = self._toll_calculator.calculate_toll(
                segment,
                truck_specs,
                business.id if business else None,
                overrides
            )
            costs[segment.country_code] = toll_cost

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

        # Get rates from settings, fall back to transport specs if not set
        base_rate = settings.rates.get("driver_base_rate")
        time_rate = settings.rates.get("driver_time_rate")
        
        self._logger.info(f"Using driver rates from settings - base_rate: {base_rate}, time_rate: {time_rate}")
        
        # Only fall back to transport specs if rates are None (not found in settings)
        if base_rate is None:
            base_rate = Decimal(str(transport.driver_specs.daily_rate))
            self._logger.info(f"Falling back to transport spec base_rate: {base_rate}")
        elif isinstance(base_rate, (int, float, str)):
            base_rate = Decimal(str(base_rate))
            
        if time_rate is None:
            time_rate = Decimal(str(transport.driver_specs.driving_time_rate))
            self._logger.info(f"Falling back to transport spec time_rate: {time_rate}")
        elif isinstance(time_rate, (int, float, str)):
            time_rate = Decimal(str(time_rate))

        # Calculate days (round up partial days)
        total_hours = Decimal(str(route.total_duration_hours))
        days = (int(total_hours) + 23) // 24
        self._logger.info(f"Calculated {days} days from {total_hours} total hours")

        # Calculate base cost using the configured rate
        base_cost = base_rate * Decimal(str(days))
        self._logger.info(f"Calculated base cost: {base_cost} ({base_rate} * {days})")

        # Calculate regular and overtime hours
        max_regular_hours = transport.driver_specs.max_driving_hours * days
        regular_hours = min(float(total_hours), float(max_regular_hours))
        overtime_hours = max(0, float(total_hours) - regular_hours)
        self._logger.info(f"Hours breakdown - regular: {regular_hours}, overtime: {overtime_hours}")

        # Calculate time-based costs using the configured rate
        regular_hours_cost = Decimal(str(regular_hours)) * time_rate
        self._logger.info(f"Regular hours cost: {regular_hours_cost} ({regular_hours} * {time_rate})")
        
        overtime_cost = (
            Decimal(str(overtime_hours)) * 
            time_rate * 
            transport.driver_specs.overtime_rate_multiplier
        )
        self._logger.info(f"Overtime cost: {overtime_cost}")

        # Calculate total cost
        total_cost = base_cost + regular_hours_cost + overtime_cost
        self._logger.info(f"Total driver cost: {total_cost}")

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

        event_costs = {}
        for event in route.timeline_events:
            # Try to get specific rate for event type, fall back to default if not found
            rate_key = f"{event.type}_rate"
            event_rate = settings.rates.get(rate_key)
            
            if event_rate is None:
                # Fall back to default rates from configuration
                from ...infrastructure.data.event_rates import EVENT_RATES
                event_rate = EVENT_RATES.get(event.type, Decimal("50"))
            
            # Convert to Decimal if needed
            if not isinstance(event_rate, Decimal):
                event_rate = Decimal(str(event_rate))
                
            event_costs[event.type] = event_rate

        self._logger.info(f"Calculated event costs for route {route.id}: {event_costs}")
        return event_costs

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

    def validate_cost_settings(self, settings: CostSettings) -> Tuple[bool, List[str]]:
        """
        Validate complete cost settings including components and rates.
        
        Args:
            settings: Cost settings to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate enabled components
        if not settings.enabled_components:
            errors.append("At least one cost component must be enabled")
            
        # Validate rates for enabled components
        required_rates = {
            "fuel": ["fuel_rate"],
            "driver": ["driver_base_rate"],
            "maintenance": ["maintenance_rate"],
            "toll": ["toll_rate_multiplier"]
        }
        
        for component in settings.enabled_components:
            if component in required_rates:
                for rate_key in required_rates[component]:
                    if rate_key not in settings.rates:
                        errors.append(f"Missing required rate '{rate_key}' for component '{component}'")
        
        # Validate rate values
        is_valid_rates, rate_errors = self.validate_rates(settings.rates)
        errors.extend(rate_errors)
        
        return len(errors) == 0, errors

    def validate_cost_calculation(self, route_id: UUID) -> Tuple[bool, List[str]]:
        """
        Validate inputs and requirements for cost calculation.
        
        Args:
            route_id: ID of the route to validate cost calculation for
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check if cost settings exist
        settings = self._settings_repo.find_by_route_id(route_id)
        if not settings:
            errors.append(f"No cost settings found for route {route_id}")
            return False, errors
            
        # Validate settings
        is_valid_settings, setting_errors = self.validate_cost_settings(settings)
        if not is_valid_settings:
            errors.extend(setting_errors)
            
        # Additional validation could be added here:
        # - Check if route exists and has required data
        # - Validate business entity permissions
        # - Check for required certifications
        # - etc.
        
        return len(errors) == 0, errors 

    def update_cost_settings(
        self,
        route_id: UUID,
        updates: Dict[str, Any]
    ) -> CostSettings:
        """
        Update cost settings with validation.
        
        Args:
            route_id: ID of the route to update settings for
            updates: Dictionary of fields to update
            
        Returns:
            Updated cost settings
            
        Raises:
            ValueError: If settings not found or validation fails
        """
        # Get existing settings
        settings = self._settings_repo.find_by_route_id(route_id)
        if not settings:
            raise ValueError("Cost settings not found. Please create settings first.")
            
        # Update enabled components if provided
        if "enabled_components" in updates:
            settings.enabled_components = updates["enabled_components"]
            
        # Update rates if provided
        if "rates" in updates:
            settings.rates = {
                k: Decimal(str(v)) for k, v in updates["rates"].items()
            }
            
        # Validate complete settings
        is_valid, errors = self.validate_cost_settings(settings)
        if not is_valid:
            raise ValueError(f"Invalid settings: {'; '.join(errors)}")
            
        # Save and return updated settings
        return self._settings_repo.save(settings)

    def get_cost_breakdown(self, route_id: UUID) -> Optional[CostBreakdown]:
        """
        Get cost breakdown for a route.
        
        Args:
            route_id: ID of the route to get breakdown for
            
        Returns:
            Cost breakdown if found, None otherwise
        """
        return self._breakdown_repo.find_by_route_id(route_id)

    def calculate_and_save_costs(
        self,
        route_id: UUID,
        transport_id: UUID,
        business_entity_id: UUID
    ) -> CostBreakdown:
        """
        Calculate and save costs for a route.
        
        Args:
            route_id: ID of the route to calculate costs for
            transport_id: ID of the transport used
            business_entity_id: ID of the business entity
            
        Returns:
            Calculated cost breakdown
            
        Raises:
            ValueError: If required entities not found or validation fails
        """
        # Validate calculation inputs
        is_valid, errors = self.validate_cost_calculation(route_id)
        if not is_valid:
            raise ValueError(f"Cost calculation validation failed: {'; '.join(errors)}")
            
        # Get required entities from repositories
        route = self._route_repo.find_by_id(route_id)
        transport = self._transport_repo.find_by_id(transport_id)
        business = self._business_repo.find_by_id(business_entity_id)
        
        if not route or not transport or not business:
            raise ValueError("Required entities not found")
            
        # Calculate costs
        breakdown = self.calculate_costs(route, transport, business)
        
        # Save and return breakdown
        return self._breakdown_repo.save(breakdown) 