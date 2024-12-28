# LoadApp.AI Domain Model - PoC Version
Version: 1.0
Last Updated: December 28, 2024

## 1. Overview

This document outlines the domain model design for LoadApp.AI PoC, focusing on the essential entities and relationships needed to support the core transport management flow.

## 2. Core Domain Entities

### 2.1 Transport Configuration

#### TransportType
Static configuration/catalog of available transport types:
```python
class TransportType:
    id: str            # "flatbed", "container", etc.
    name: str          # Display name
    truck_specifications: TruckSpecification
    driver_specifications: DriverSpecification
```

#### TruckSpecification
Truck-specific configuration values:
```python
class TruckSpecification:
    fuel_consumption_empty: float     # L/km
    fuel_consumption_loaded: float    # L/km
    toll_class: str                  # For toll calculations
    euro_class: str                  # For toll calculations
    co2_class: str                   # For emissions
    maintenance_rate_per_km: Decimal
```

#### DriverSpecification
Driver-specific configuration values:
```python
class DriverSpecification:
    daily_rate: Decimal
    required_license_type: str
    required_certifications: List[str]
```

### 2.2 Runtime Entities

#### Transport
Runtime instance created when user selects transport type:
```python
class Transport:
    id: UUID
    transport_type_id: str           # References TransportType
    business_entity_id: UUID
    truck_specs: TruckSpecification  # Copied from TransportType
    driver_specs: DriverSpecification # Copied from TransportType
    is_active: bool = True
```

#### Route
Represents a transport route with timeline:
```python
class Route:
    id: UUID
    transport_id: UUID
    business_entity_id: UUID
    cargo_id: UUID
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    empty_driving: EmptyDriving      # Fixed 200km/4h for PoC
    timeline_events: List[TimelineEvent]
    country_segments: List[CountrySegment]
    total_distance_km: float
    total_duration_hours: float
    is_feasible: bool = True         # Always true for PoC
```

#### BusinessEntity
Represents a transport company:
```python
class BusinessEntity:
    id: UUID
    name: str
    certifications: List[str]
    operating_countries: List[str]
    cost_overheads: Dict[str, Decimal]
```

#### Cargo
Cargo being transported:
```python
class Cargo:
    id: UUID
    weight: float
    value: Decimal
    special_requirements: List[str]
```

### 2.3 Value Objects

#### Location
```python
class Location:
    latitude: float
    longitude: float
    address: str
```

#### EmptyDriving
```python
class EmptyDriving:
    distance_km: float = 200.0      # Fixed for PoC
    duration_hours: float = 4.0     # Fixed for PoC
```

#### TimelineEvent
```python
class TimelineEvent:
    id: UUID
    type: str                      # pickup/rest/delivery
    location: Location
    planned_time: datetime
    duration_hours: float = 1.0    # Fixed for PoC
    event_order: int
```

#### CountrySegment
```python
class CountrySegment:
    country_code: str
    distance_km: float
    duration_hours: float
```

## 3. Cost-Related Entities

### CostSettings
```python
class CostSettings:
    id: UUID
    route_id: UUID
    enabled_components: List[str]    # Which costs are active
    rates: Dict[str, Decimal]        # Cost rates per component
    business_entity_id: UUID         # For overhead costs
```

### CostBreakdown
```python
class CostBreakdown:
    route_id: UUID
    fuel_costs: Dict[str, Decimal]   # Per country
    toll_costs: Dict[str, Decimal]   # Per country
    driver_costs: Decimal
    overhead_costs: Decimal
    timeline_event_costs: Dict[str, Decimal]
    total_cost: Decimal
```

### Offer
```python
class Offer:
    id: UUID
    route_id: UUID
    cost_breakdown_id: UUID
    margin_percentage: Decimal
    final_price: Decimal
    ai_content: Optional[str]        # AI enhancement
    fun_fact: Optional[str]          # Transport fun fact
    created_at: datetime
```

## 4. Core Flow Interactions

### Transport Type Selection
1. User selects transport_type (e.g., "flatbed")
2. System:
   - Looks up TransportType configuration
   - Creates Transport instance with specifications
   - Uses Transport for subsequent operations

### Route Creation
1. Transport instance assigned to Route
2. Empty driving automatically added (200km/4h)
3. Timeline events created:
   - Pickup (1h)
   - One rest in middle (1h)
   - Delivery (1h)

### Cost Calculation
Uses specifications from Transport instance:
- Fuel costs based on consumption rates
- Toll costs based on truck classes
- Driver costs based on daily rate
- Additional timeline event costs

## 5. Key Design Decisions

### Simplified Fleet Management
- No separate Truck/Driver entities needed for PoC
- Transport combines truck/driver specifications
- All configuration in TransportType

### Fixed Values for PoC
- Empty driving: 200km/4h
- Event duration: 1h each
- Route always feasible
- One rest event in middle

### Clean Separation
- Static configuration (TransportType)
- Runtime instances (Transport)
- Route planning (Route + Timeline)
- Cost management (Settings + Breakdown)

## 6. Future Evolution

### Potential Extensions
- Real truck/driver management
- Dynamic empty driving calculation
- Multiple rest events
- Real feasibility checks
- Advanced cost configurations

### Migration Path
1. Keep TransportType as configuration
2. Add real Truck/Driver entities
3. Enhance Transport to link physical resources
4. Expand cost calculation logic
