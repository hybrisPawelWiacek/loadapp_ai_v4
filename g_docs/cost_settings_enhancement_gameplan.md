# Cost Settings Enhancement Gameplan
Version: 1.0
Last Updated: 2024-01-08

## Overview

This document outlines the implementation plan for enhancing cost settings functionality in LoadApp.AI, focusing on:
- Fuel rates configuration and country-specific rates
- Event costs differentiation
- Business overhead visibility
- Toll rates for additional countries
- Enhanced API endpoints

## 1. Backend Implementation

### 1.1 New Configuration Files

#### A. Fuel Rates (`backend/infrastructure/data/fuel_rates.py`):
```python
from decimal import Decimal

DEFAULT_FUEL_RATES = {
    "DE": Decimal("1.85"),  # Germany
    "PL": Decimal("1.65"),  # Poland
}

# Consumption rates (L/km)
CONSUMPTION_RATES = {
    "empty": Decimal("0.22"),    # Empty driving
    "loaded": Decimal("0.29"),   # Loaded driving
    "per_ton": Decimal("0.03")   # Additional per ton of cargo
}
```

#### B. Event Rates (`backend/infrastructure/data/event_rates.py`):
```python
from decimal import Decimal

EVENT_RATES = {
    "pickup": Decimal("50.00"),
    "delivery": Decimal("50.00"),
    "rest": Decimal("30.00")     # Different rate for rest stops
}

EVENT_RATE_RANGES = {
    "pickup": (Decimal("20.00"), Decimal("200.00")),
    "delivery": (Decimal("20.00"), Decimal("200.00")),
    "rest": (Decimal("20.00"), Decimal("150.00"))
}
```

#### C. Update Toll Rates (`backend/infrastructure/data/toll_rates.py`):
```python
# Add Poland to DEFAULT_TOLL_RATES
"PL": {  
    "toll_class": {
        "1": Decimal("0.167"),
        "2": Decimal("0.188"),
        "3": Decimal("0.208"),
        "4": Decimal("0.228")
    },
    "euro_class": {
        "VI": Decimal("0.000"),
        "V": Decimal("0.021"),
        "IV": Decimal("0.042"),
        "III": Decimal("0.063")
    }
}
```

### 1.2 API Endpoints

#### A. New Endpoints (`backend/api/routes/cost_routes.py`):
```python
@router.get("/api/cost/rates/fuel/<route_id>")
def get_fuel_rates(route_id: UUID):
    """Get default fuel rates for countries in the route."""
    route = route_service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Get current settings if they exist
    current_settings = cost_service.get_settings(route_id)
    
    # Get countries from route segments
    countries = {segment.country_code for segment in route.country_segments}
    
    # Filter default rates for route countries
    default_rates = {
        country: DEFAULT_FUEL_RATES[country]
        for country in countries
        if country in DEFAULT_FUEL_RATES
    }
    
    response = {
        "default_rates": default_rates,
        "consumption_rates": CONSUMPTION_RATES,
    }
    
    # Add current settings if they exist
    if current_settings and current_settings.rates:
        response["current_settings"] = {
            k: v for k, v in current_settings.rates.items()
            if k.startswith("fuel_rate_") and k.split("_")[-1] in countries
        }
    
    return response

@router.get("/api/cost/rates/toll/<route_id>")
def get_toll_rates(route_id: UUID):
    """Get toll rates for countries in the route."""
    route = route_service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Get transport details for vehicle class info
    transport = transport_service.get_transport(route.transport_id)
    
    # Get current settings if they exist
    current_settings = cost_service.get_settings(route_id)
    
    # Get countries from route segments
    countries = {segment.country_code for segment in route.country_segments}
    
    response = {
        "default_rates": {
            country: {
                "toll_class_rates": DEFAULT_TOLL_RATES[country]["toll_class"],
                "euro_class_adjustments": DEFAULT_TOLL_RATES[country]["euro_class"]
            }
            for country in countries
            if country in DEFAULT_TOLL_RATES
        },
        "vehicle_info": {
            "toll_class": transport.truck_specs.toll_class,
            "euro_class": transport.truck_specs.euro_class,
            "toll_class_description": get_toll_class_description(transport.truck_specs.toll_class),
            "euro_class_description": get_euro_class_description(transport.truck_specs.euro_class)
        }
    }
    
    # Add current settings if they exist
    if current_settings and current_settings.rates:
        response["current_settings"] = {
            k: v for k, v in current_settings.rates.items()
            if k.startswith("toll_rate_") and k.split("_")[-1] in countries
        }
    
    # Add business entity overrides if they exist
    if route.business_entity_id:
        overrides = toll_rate_override_repo.find_for_business_multiple(
            business_entity_id=route.business_entity_id,
            countries=list(countries),
            vehicle_class=transport.truck_specs.toll_class
        )
        if overrides:
            response["business_overrides"] = {
                override.country_code: {
                    "rate_multiplier": str(override.rate_multiplier),
                    "route_type": override.route_type
                }
                for override in overrides
            }
    
    return response

@router.get("/api/cost/rates/event")
def get_event_rates():
    """Get default event rates and allowed ranges."""
    return {
        "rates": EVENT_RATES,
        "ranges": EVENT_RATE_RANGES
    }
```

#### B. Modified Endpoints:
```python
@router.post("/api/cost/settings/{route_id}")
def create_cost_settings(route_id: UUID, settings: CostSettingsCreate):
    """Enhanced create cost settings endpoint."""
    validate_rates(settings.rates)
    validate_event_rates(settings.rates)
    return cost_service.create_settings(route_id, settings)

@router.get("/api/cost/settings/{route_id}")
def get_cost_settings(route_id: UUID):
    """Enhanced get cost settings endpoint."""
    settings = cost_service.get_settings(route_id)
    if settings:
        settings.fuel_rates = settings.fuel_rates or DEFAULT_FUEL_RATES
        settings.event_rates = settings.event_rates or EVENT_RATES
    return settings
```

### 1.3 Domain Models

#### A. New Models (`backend/domain/entities/cost.py`):
```python
class FuelRates(BaseModel):
    country_rates: Dict[str, Decimal]
    consumption_rates: Dict[str, Decimal]

class EventRates(BaseModel):
    rates: Dict[str, Decimal]
    ranges: Dict[str, Tuple[Decimal, Decimal]]

class CostSettingsCreate(BaseModel):
    enabled_components: List[str]
    rates: Dict[str, Union[Decimal, Dict[str, Decimal]]]
    fuel_rates: Optional[Dict[str, Decimal]]
    event_rates: Optional[Dict[str, Dict[str, Decimal]]]

class CostBreakdownResponse(BaseModel):
    id: UUID
    route_id: UUID
    fuel_costs: Dict[str, Decimal]
    toll_costs: Dict[str, Decimal]
    driver_costs: Dict[str, Decimal]
    overhead_costs: Decimal
    timeline_event_costs: Dict[str, Dict[str, Decimal]]
    total_cost: Decimal
```

### 1.3 Repository Updates

#### A. Toll Rate Override Repository (`backend/infrastructure/repositories/toll_rate_override_repository.py`):
```python
class TollRateOverrideRepository:
    """Repository for toll rate overrides."""

    def __init__(self, session):
        self._session = session

    def find_by_id(self, id: UUID) -> Optional[TollRateOverride]:
        """Find toll rate override by ID."""
        model = self._session.query(TollRateOverrideModel).filter_by(id=str(id)).first()
        return self._to_entity(model) if model else None

    def find_for_business(
        self,
        business_entity_id: UUID,
        country_code: str,
        vehicle_class: str
    ) -> Optional[TollRateOverride]:
        """Find toll rate override for a business entity, country and vehicle class."""
        model = (
            self._session.query(TollRateOverrideModel)
            .filter_by(
                business_entity_id=str(business_entity_id),
                country_code=country_code,
                vehicle_class=vehicle_class
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def find_for_business_multiple(
        self,
        business_entity_id: UUID,
        countries: List[str],
        vehicle_class: str
    ) -> List[TollRateOverride]:
        """Find toll rate overrides for multiple countries."""
        models = (
            self._session.query(TollRateOverrideModel)
            .filter(
                TollRateOverrideModel.business_entity_id == str(business_entity_id),
                TollRateOverrideModel.country_code.in_(countries),
                TollRateOverrideModel.vehicle_class == vehicle_class
            )
            .all()
        )
        return [self._to_entity(model) for model in models]

    def save(self, override: TollRateOverride) -> TollRateOverride:
        """Save a toll rate override."""
        model = TollRateOverrideModel(
            id=str(override.id),
            vehicle_class=override.vehicle_class,
            rate_multiplier=override.rate_multiplier,
            country_code=override.country_code,
            route_type=override.route_type,
            business_entity_id=str(override.business_entity_id)
        )
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: TollRateOverrideModel) -> TollRateOverride:
        """Convert model to domain entity."""
        return TollRateOverride(
            id=UUID(model.id),
            vehicle_class=model.vehicle_class,
            rate_multiplier=model.rate_multiplier,
            country_code=model.country_code,
            route_type=model.route_type,
            business_entity_id=UUID(model.business_entity_id)
        )
```

## 2. Frontend Implementation

### 2.1 Cost Settings View Updates (`frontend/views/view_cost.py`)

#### A. Fuel Rates Section:
```python
with st.expander("⛽ Fuel Rates"):
    st.markdown("Set fuel rates per country:")
    
    # Show consumption rates info
    st.info("""Default Consumption Rates:
    - Empty driving: 0.22 L/km
    - Loaded driving: 0.29 L/km
    - Additional per ton: 0.03 L/km""")
    
    # Fetch default and current rates for the route
    route_id = st.session_state.get('route_id')
    if route_id:
        fuel_rates = api_request(f"/api/cost/rates/fuel/{route_id}")
        if fuel_rates:
            default_rates = fuel_rates.get('default_rates', {})
            current_settings = fuel_rates.get('current_settings', {})
            
            # Country-specific rates
            route = st.session_state.get('route_data', {})
            for segment in route.get('country_segments', []):
                country = segment.get('country_code')
                if country:
                    # Get current rate if exists, otherwise use default
                    current_rate = current_settings.get(f'fuel_rate_{country}')
                    default_rate = default_rates.get(country, 1.5)
                    
                    rate = st.number_input(
                        f"Fuel Rate for {country} (EUR/L)",
                        min_value=0.5,
                        max_value=5.0,
                        value=float(current_rate if current_rate else default_rate),
                        step=0.1,
                        help=f"Set fuel rate for {country} (0.50-5.00 EUR/L)"
                    )
                    if validate_rate('fuel_rate', rate):
                        rates[f'fuel_rate_{country}'] = rate
                    else:
                        st.error(f"Invalid fuel rate for {country}")
```

#### B. Toll Rates Section:
```python
with st.expander("🛣️ Toll Rates"):
    st.markdown("Configure toll rates per country:")
    
    # Fetch toll rates for the route
    route_id = st.session_state.get('route_id')
    if route_id:
        toll_rates = api_request(f"/api/cost/rates/toll/{route_id}")
        if toll_rates:
            # Show vehicle information
            vehicle_info = toll_rates.get('vehicle_info', {})
            st.info(f"""Vehicle Classification:
            - Toll Class: {vehicle_info.get('toll_class_description')}
            - Euro Class: {vehicle_info.get('euro_class_description')}""")
            
            # Show rates per country
            default_rates = toll_rates.get('default_rates', {})
            current_settings = toll_rates.get('current_settings', {})
            business_overrides = toll_rates.get('business_overrides', {})
            
            for segment in route.get('country_segments', []):
                country = segment.get('country_code')
                if country:
                    # Calculate default rate for this vehicle
                    country_rates = default_rates.get(country, {})
                    base_rate = country_rates.get('toll_class_rates', {}).get(vehicle_info['toll_class'], 0)
                    euro_adjustment = country_rates.get('euro_class_adjustments', {}).get(vehicle_info['euro_class'], 0)
                    default_rate = base_rate + euro_adjustment
                    
                    # Show business override if exists
                    override = business_overrides.get(country)
                    if override:
                        st.info(f"Business rate multiplier for {country}: {override['rate_multiplier']}x")
                    
                    # Get current rate if exists, otherwise use default
                    current_rate = current_settings.get(f'toll_rate_{country}')
                    
                    rate = st.number_input(
                        f"Toll Rate for {country} (EUR/km)",
                        min_value=0.1,
                        max_value=2.0,
                        value=float(current_rate if current_rate else default_rate),
                        step=0.01,
                        help=f"Set toll rate for {country} (0.10-2.00 EUR/km)"
                    )
                    if validate_rate('toll_rate', rate):
                        rates[f'toll_rate_{country}'] = rate
                    else:
                        st.error(f"Invalid toll rate for {country}")
```

#### C. Business Overhead Section:
```python
with st.expander("💼 Business Overhead"):
    st.markdown("Pre-configured Business Overhead Costs:")
    
    if business and business.cost_overheads:
        for cost_type, amount in business.cost_overheads.items():
            st.text_input(
                f"{cost_type.title()}",
                value=format_currency(amount),
                disabled=True,
                help="Pre-configured overhead cost"
            )
    else:
        st.warning("No business overhead costs configured")
```

#### D. Event Costs Section:
```python
with st.expander("📅 Event Costs"):
    st.markdown("Set costs for timeline events:")
    
    for event_type, (min_rate, max_rate) in EVENT_RATE_RANGES.items():
        rate = st.number_input(
            f"{event_type.title()} Event Rate (EUR/event)",
            min_value=float(min_rate),
            max_value=float(max_rate),
            value=float(EVENT_RATES[event_type]),
            step=10.0,
            help=f"Set rate for {event_type} events ({min_rate}-{max_rate} EUR/event)"
        )
        if validate_rate(f'{event_type}_rate', rate):
            rates[f'{event_type}_rate'] = rate
```

### 2.2 Cost Utilities Update (`frontend/utils/cost_utils.py`)

```python
def fetch_route_fuel_rates(route_id: str) -> Optional[Dict]:
    """Fetch fuel rates specific to a route's countries."""
    return api_request(f"/api/cost/rates/fuel/{route_id}", method="GET")

def fetch_event_rates() -> Optional[Dict]:
    """Fetch event rates and ranges."""
    return api_request("/api/cost/rates/event", method="GET")

def validate_rate(rate_type: str, value: float) -> bool:
    """Enhanced rate validation."""
    if rate_type == 'fuel_rate':
        return 0.5 <= value <= 5.0
    elif rate_type.endswith('_rate'):
        event_type = rate_type.replace('_rate', '')
        min_rate, max_rate = EVENT_RATE_RANGES.get(event_type, (20.0, 200.0))
        return min_rate <= value <= max_rate
    return True
```

## 3. Implementation Order

### Phase 1: Backend Foundation
1. Create new configuration files
   - fuel_rates.py
   - event_rates.py
   - Update toll_rates.py

2. Add new domain models
   - Update cost.py with new models
   - Add validation logic

3. Implement new endpoints
   - Add rate endpoints
   - Modify existing endpoints

### Phase 2: Frontend Updates
1. Update cost utilities
   - Add rate fetching functions
   - Enhance validation logic

2. Update cost settings view
   - Add fuel rates section
   - Add business overhead display
   - Update event costs section

### Phase 3: Testing
1. Backend tests
   - Test new configuration files
   - Test endpoint functionality
   - Test rate validation

2. Frontend tests
   - Test UI components
   - Test rate validation
   - Test API integration

## 4. Testing Requirements

### 4.1 Backend Tests
```python
# Test new endpoints
def test_get_fuel_rates():
    """Test fuel rates endpoint."""

def test_get_event_rates():
    """Test event rates endpoint."""

def test_get_toll_rates():
    """Test toll rates endpoint."""

# Test rate validation
def test_validate_fuel_rates():
    """Test fuel rate validation."""

def test_validate_event_rates():
    """Test event rate validation."""
```

### 4.2 Frontend Tests
```python
# Test UI components
def test_fuel_rates_display():
    """Test fuel rates section rendering."""

def test_business_overhead_display():
    """Test business overhead section rendering."""

def test_event_costs_display():
    """Test event costs section rendering."""

# Test validation
def test_rate_validation():
    """Test rate validation in UI."""
```

## 5. Validation Rules

### 5.1 Fuel Rates
- Range: 0.50 - 5.00 EUR/L
- Required for each country in route
- Different rates for DE vs PL

### 5.2 Driver Costs
- Daily Base Rate: 100.00 - 500.00 EUR/day
- Time-based Rate: 10.00 - 100.00 EUR/hour
- Overtime Multiplier: 1.0 - 2.0

### 5.3 Event Costs
- Pickup/Delivery: 20.00 - 200.00 EUR/event
- Rest Stops: 20.00 - 150.00 EUR/event

### 5.4 Business Overhead
- Interactive configuration of overhead costs per route
- Categories:
  - Administration costs (0.01 - 1000.00 EUR/route)
  - Insurance costs (0.01 - 1000.00 EUR/route)
  - Facilities costs (0.01 - 1000.00 EUR/route)
  - Other costs (0.00 - 1000.00 EUR/route)
- Features:
  - Display current overhead costs from business entity
  - Allow modification of costs per route
  - Validate rate ranges
  - Update business entity with new overhead costs
  - Include in total cost calculation if enabled

#### A. Business Overhead API Endpoints:
```python
@router.put("/api/business/<business_id>/overheads")
def update_business_overheads(business_id: str):
    """Update business overhead costs."""
    return {
        "cost_overheads": {
            "admin": "100.00",
            "insurance": "250.00",
            "facilities": "150.00",
            "other": "0.00"
        }
    }
```

#### B. Cost Service Updates:
```python
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
```

#### C. Frontend Implementation:
```python
with st.expander("💼 Business Overhead Costs"):
    st.markdown("Configure business overhead costs:")
    
    # Get business entity from session state
    business_entity = st.session_state.get('selected_business_entity')
    if business_entity:
        # Display current overheads
        current_overheads = business_entity.get('cost_overheads', {})
        st.write("Current Overhead Costs:")
        
        # Administration costs
        admin_cost = st.number_input(
            "Administration Costs (EUR/route)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_overheads.get('admin', 100.0)),
            step=10.0,
            help="Set administrative overhead costs per route"
        )
        
        # Insurance costs
        insurance_cost = st.number_input(
            "Insurance Costs (EUR/route)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_overheads.get('insurance', 250.0)),
            step=10.0,
            help="Set insurance overhead costs per route"
        )
        
        # Facilities costs
        facilities_cost = st.number_input(
            "Facilities Costs (EUR/route)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_overheads.get('facilities', 150.0)),
            step=10.0,
            help="Set facilities overhead costs per route"
        )
        
        # Other overhead costs
        other_cost = st.number_input(
            "Other Overhead Costs (EUR/route)",
            min_value=0.0,
            max_value=1000.0,
            value=float(current_overheads.get('other', 0.0)),
            step=10.0,
            help="Set any other overhead costs per route"
        )
```

#### D. Rate Validation:
```python
RATE_RANGES = {
    'overhead_admin_rate': (0.01, 1000.0),
    'overhead_insurance_rate': (0.01, 1000.0),
    'overhead_facilities_rate': (0.01, 1000.0),
    'overhead_other_rate': (0.0, 1000.0)
}

def validate_rate(rate_type: str, value: float) -> bool:
    """Validate overhead rate values."""
    if rate_type not in RATE_RANGES:
        return False
    min_val, max_val = RATE_RANGES[rate_type]
    return min_val <= value <= max_val
```

#### E. Data Flow:
1. Frontend loads business entity's current overhead costs
2. User can modify overhead costs within defined ranges
3. On save:
   - Validate all rates
   - Update business entity via API
   - Include new rates in cost settings
   - Recalculate total costs
4. Changes persist in both:
   - Business entity configuration
   - Route-specific cost settings

## 6. Migration Steps

1. Create new configuration files
2. Update database models if needed
3. Add new endpoints
4. Update frontend components
5. Run tests
6. Deploy changes

## 7. Documentation Updates

1. Update API documentation
2. Update frontend documentation
3. Update testing documentation
4. Update deployment documentation 

## 8. Progress Tracking

### Backend Implementation Status
- [ ] Configuration Files
  - [ ] Create fuel_rates.py
  - [ ] Create event_rates.py
  - [ ] Update toll_rates.py with Poland data

- [ ] API Endpoints
  - [ ] GET /api/cost/rates/fuel/<route_id>
  - [ ] GET /api/cost/rates/toll/<route_id>
  - [ ] GET /api/cost/rates/event
  - [ ] Modify existing cost settings endpoints

- [ ] Domain Models
  - [ ] Add FuelRates model
  - [ ] Add EventRates model
  - [ ] Update CostSettingsCreate model
  - [ ] Update CostBreakdownResponse model

- [ ] Repository Updates
  - [ ] Implement TollRateOverrideRepository
  - [ ] Add business entity override methods

### Frontend Implementation Status
- [ ] Cost Utilities Update
  - [ ] Add rate fetching functions
  - [ ] Enhance validation logic

- [ ] Cost Settings View Updates
  - [ ] Fuel Rates Section
    - [ ] Display consumption rates info
    - [ ] Integrate with fuel rates API
    - [ ] Show current/default rates
  
  - [ ] Toll Rates Section
    - [ ] Display vehicle classification
    - [ ] Integrate with toll rates API
    - [ ] Show business overrides
    - [ ] Default rate calculation
  
  - [ ] Event Costs Section
    - [ ] Separate rates by event type
    - [ ] Integrate with event rates API
    - [ ] Event-specific ranges

### Testing Status
- [ ] Backend Tests
  - [ ] Test new configuration files
  - [ ] Test API endpoints
  - [ ] Test rate validation
  - [ ] Test repository methods

- [ ] Frontend Tests
  - [ ] Test UI components
  - [ ] Test rate validation
  - [ ] Test API integration

### Documentation Status
- [ ] API Documentation
- [ ] Frontend Documentation
- [ ] Testing Documentation
- [ ] Deployment Documentation

### Notes
- Use this section to track any issues, blockers, or decisions made during implementation
- Update status regularly (✓ for completed, - for in progress, × for blocked)
- Add comments for any deviations from original plan 