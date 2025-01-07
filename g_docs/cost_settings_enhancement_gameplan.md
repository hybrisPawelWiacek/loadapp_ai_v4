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
@router.get("/api/cost/rates/fuel")
def get_fuel_rates():
    """Get default fuel rates by country."""
    return {
        "rates": DEFAULT_FUEL_RATES,
        "consumption": CONSUMPTION_RATES
    }

@router.get("/api/cost/rates/event")
def get_event_rates():
    """Get default event rates and allowed ranges."""
    return {
        "rates": EVENT_RATES,
        "ranges": EVENT_RATE_RANGES
    }

@router.get("/api/cost/rates/toll/{country_code}")
def get_toll_rates(country_code: str):
    """Get toll rates for specific country."""
    return {
        "rates": DEFAULT_TOLL_RATES.get(country_code, {}),
        "ranges": TOLL_RATE_RANGES
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
    
    # Country-specific rates
    route = st.session_state.get('route_data', {})
    for segment in route.get('country_segments', []):
        country = segment.get('country_code')
        if country:
            rate = st.number_input(
                f"Fuel Rate for {country} (EUR/L)",
                min_value=0.5,
                max_value=5.0,
                value=DEFAULT_FUEL_RATES.get(country, 1.5),
                step=0.1,
                help=f"Set fuel rate for {country} (0.50-5.00 EUR/L)"
            )
```

#### B. Business Overhead Section:
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

#### C. Event Costs Section:
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
def fetch_default_rates():
    """Fetch all default rates from backend."""
    fuel_rates = api_request("/api/cost/rates/fuel", method="GET")
    event_rates = api_request("/api/cost/rates/event", method="GET")
    return {
        "fuel": fuel_rates,
        "event": event_rates
    }

def validate_rate(rate_type: str, value: float) -> bool:
    """Enhanced rate validation."""
    if rate_type.startswith('fuel_'):
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
- Display only (no user input)
- Show breakdown by category
- Include in total if enabled

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