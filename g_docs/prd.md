# LoadApp.AI Product Requirements Document
Version: Final PoC
Last Updated: December 28, 2024

## 1. Overview

LoadApp.AI enables transport managers to efficiently plan routes, calculate costs, and generate offers. This document maps business requirements to technical implementation for the PoC version.

## FILES TO REFERENCE:

g_docs/business_req.md

## project structure:
.
├── README.md
├── backend
│   ├── __init__.py
│   ├── alembic.ini
│   ├── api
│   │   └── routes
│   │       ├── business_routes.py
│   │       ├── cargo_routes.py
│   │       ├── cost_routes.py
│   │       ├── location_routes.py
│   │       ├── offer_routes.py
│   │       ├── route_routes.py
│   │       └── transport_routes.py
│   ├── app.py
│   ├── config.py
│   ├── database
│   │   ├── loadapp.db
│   │   ├── loadapp.db-shm
│   │   └── loadapp.db-wal
│   ├── domain
│   │   ├── __init__.py
│   │   ├── entities
│   │   │   ├── __init__.py
│   │   │   ├── business.py
│   │   │   ├── cargo.py
│   │   │   ├── location.py
│   │   │   ├── rate_types.py
│   │   │   ├── route.py
│   │   │   └── transport.py
│   │   └── services
│   │       ├── business_service.py
│   │       ├── cargo_service.py
│   │       ├── cost_service.py
│   │       ├── location_service.py
│   │       ├── offer_service.py
│   │       ├── route_service.py
│   │       └── transport_service.py
│   ├── infrastructure
│   │   ├── __init__.py
│   │   ├── adapters
│   │   │   ├── google_maps_adapter.py
│   │   │   ├── openai_adapter.py
│   │   │   └── toll_rate_adapter.py
│   │   ├── container.py
│   │   ├── data
│   │   │   └── toll_rates.py
│   │   ├── database.py
│   │   ├── external_services
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py
│   │   │   ├── google_maps_service.py
│   │   │   ├── openai_service.py
│   │   │   └── toll_rate_service.py
│   │   ├── logging.py
│   │   ├── migrations
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── business_models.py
│   │   │   ├── cargo_models.py
│   │   │   ├── rate_models.py
│   │   │   ├── route_models.py
│   │   │   └── transport_models.py
│   │   └── repositories
│   │       ├── base.py
│   │       ├── business_repository.py
│   │       ├── cargo_repository.py
│   │       ├── empty_driving_repository.py
│   │       ├── location_repository.py
│   │       ├── rate_validation_repository.py
│   │       ├── route_repository.py
│   │       ├── toll_rate_override_repository.py
│   │       └── transport_repository.py
│   ├── loadapp.db-shm
│   ├── loadapp.db-wal
│   ├── migrations
│   │   ├── README
│   │   ├── __init__.py
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions
│   │       ├── 20250106_2203_23f1a3b2f42e_base_migration.py
│   │       ├── 20250106_2340_add_status_and_actual_time_to_timeline_events.py
│   │       └── 20250107_0023_add_segment_type_to_country_segments.py
│   └── scripts
│       ├── init_db.py
│       ├── seed_data.py
│       └── seed_transports.py
├── cache
├── docs
│   ├── TESTING_SETUP.MD
│   ├── api_endpoints.md
│   └── system_architecture_v1.md
├── frontend
│   ├── __init__.py
│   ├── app_main.py
│   ├── cache
│   ├── src
│   │   └── utils
│   │       └── map_utils.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── cargo_utils.py
│   │   ├── cost_utils.py
│   │   ├── map_utils.py
│   │   ├── offer_utils.py
│   │   ├── route_utils.py
│   │   └── shared_utils.py
│   └── views
│       ├── __init__.py
│       ├── view_cargo.py
│       ├── view_cost.py
│       ├── view_history.py
│       ├── view_input.py
│       ├── view_offer.py
│       └── view_route.py
├── g_docs
│   ├── archive
│   │   ├── cargo_implementation_gameplan.md
│   │   ├── combined_rules.md
│   │   ├── implementation_gameplan.md
│   │   ├── implementation_guidelines.md
│   │   ├── poc_enhancement_gameplan.md
│   │   ├── service_layer_refactoring_plan.md
│   │   ├── status_history_debug_summary.md
│   │   ├── testing_requirements.md
│   │   └── validation_details_debug.md
│   ├── business_req.md
│   ├── domain_layer_cons.md
│   ├── prd.md
│   └── tonewtogo
│       ├── business_entity_gameplan_DONOTUSE.md
│       ├── new_frontend_gameplan_DONOTUSE.md
│       ├── prd_addendum.md
│       └── system_architecture_post_POC_DONOTUSE.md
├── k_docs
├── loadapp.db
├── loadapp.db-shm
├── loadapp.db-wal
├── pytest.ini
├── requirements.txt
├── scripts
│   ├── run_tests.sh
│   ├── start_backend.sh
│   └── start_frontend.sh
├── template.env
└── tests
    ├── __init__.py
    ├── backend
    │   ├── __init__.py
    │   ├── api
    │   │   └── routes
    │   │       ├── test_business_routes.py
    │   │       ├── test_cargo_routes.py
    │   │       ├── test_cost_routes.py
    │   │       ├── test_location_routes.py
    │   │       ├── test_offer_routes.py
    │   │       ├── test_route_routes.py
    │   │       └── test_transport_routes.py
    │   ├── domain
    │   │   ├── entities
    │   │   │   ├── test_business.py
    │   │   │   ├── test_cargo.py
    │   │   │   ├── test_location.py
    │   │   │   ├── test_route.py
    │   │   │   └── test_transport.py
    │   │   └── services
    │   │       ├── test_business_service.py
    │   │       ├── test_cargo_service.py
    │   │       ├── test_cost_service.py
    │   │       ├── test_location_service.py
    │   │       ├── test_offer_service.py
    │   │       ├── test_route_service.py
    │   │       └── test_transport_service.py
    │   ├── external_services
    │   │   ├── conftest.py
    │   │   ├── test_google_maps_service.py
    │   │   ├── test_openai_service.py
    │   │   └── test_toll_rate_service.py
    │   ├── infrastructure
    │   │   ├── adapters
    │   │   │   └── test_toll_rate_adapter.py
    │   │   ├── models
    │   │   │   ├── test_business_models.py
    │   │   │   ├── test_cargo_models.py
    │   │   │   ├── test_route_models.py
    │   │   │   └── test_transport_models.py
    │   │   └── repositories
    │   │       ├── test_business_repository.py
    │   │       ├── test_cargo_repository.py
    │   │       ├── test_location_repository.py
    │   │       ├── test_route_repository.py
    │   │       └── test_transport_repository.py
    │   ├── manual
    │   │   ├── __init__.py
    │   │   └── test_google_maps.py
    │   └── test_app.py
    ├── conftest.py
    └── frontend
        ├── __init__.py
        ├── cache
        ├── conftest.py
        ├── pytest.ini
        ├── test_app_main.py
        ├── test_utils
        │   ├── test_cargo_utils.py
        │   ├── test_offer_utils.py
        │   └── test_shared_utils.py
        └── test_views
            ├── test_view_cargo.py
            ├── test_view_cost.py
            ├── test_view_input.py
            ├── test_view_offer.py
            └── test_view_route.py


## 2. Core Transport Manager Flow

### Phase 1: Route & Transport Type Input

#### Business Requirements
1. User provides:
   - Origin and destination locations
   - Transport type selection (flatbed/livestock/container/plandeka/oversized)
   - Pickup and delivery times
   - Cargo details (weight, value, special requirements)

#### Technical Implementation
1. Entities Used:
   ```python
   # Static configuration
   TransportType:
     - truck_specifications (fuel rates, toll class)
     - driver_specifications (daily rate)

   # Runtime instance
   Transport:
     - Created from TransportType
     - Contains specs for calculations

   # Cargo details
   Cargo:
     - Basic PoC fields only
     - Links to Route
   ```

2. Data Flow:
   - User selects transport_type
   - System creates Transport instance
   - Cargo entity created
   - Both linked to new Route

### Phase 2: Route Calculation

#### Business Requirements
1. System calculates:
   - Route segments by country
   - Empty driving from truck's current location to cargo pickup
   - Timeline events (pickup, rest stops, delivery)
   - Total distance and duration

2. Empty Driving:
   - Dynamic calculation based on truck's current location
   - Uses Google Maps API for accurate distance/duration
   - Visualized as dashed green line on the map
   - Distance and duration based on actual route
   - Includes start location (truck) and end location (cargo pickup)

3. Route Segments:
   - Split by country borders
   - Each segment includes:
     * Start/end coordinates
     * Distance and duration
     * Country-specific details for cost calculation
   - Visualized on map with country-specific colors

4. Timeline Events:
   - Pickup at origin
   - Rest stops (calculated based on driving hours)
   - Delivery at destination
   - Each event includes:
     * Location (address, coordinates)
     * Planned time
     * Duration
     * Type (pickup/rest/delivery)

#### Technical Implementation
1. Route Entity Structure:
   ```python
   Route:
     - transport_id: UUID
     - cargo_id: UUID
     - truck_location_id: UUID  # Current truck location
     - origin_id: UUID
     - destination_id: UUID
     - pickup_time: datetime
     - delivery_time: datetime
     - empty_driving: EmptyDriving
     - country_segments: List[CountrySegment]
     - timeline_events: List[TimelineEvent]
     - total_distance_km: Decimal
     - total_duration_hours: Decimal
     - status: RouteStatus
   
   EmptyDriving:
     - start_location_id: UUID  # Truck location
     - end_location_id: UUID    # Cargo pickup location
     - distance_km: Decimal
     - duration_hours: Decimal
     - route_points: List[Coordinates]  # For map visualization
   ```

2. Route Calculation Process:
   a. Validate inputs (locations, times, etc.)
   b. Calculate empty driving segment from truck to pickup
   c. Calculate main route segments
   d. Generate timeline events
   e. Compute total distance and duration

### Phase 3: Cost Management

#### Business Requirements
1. Cost Settings Configuration:
   - Display settings form
   - Configure components
   - Save per route

2. Cost Calculation:
   - Process enabled components
   - Calculate country-specific costs
   - Generate breakdown

#### Technical Implementation
1. Entities Used:
   ```python
   CostSettings:
     - enabled_components
     - rates
     - business_entity_id

   CostBreakdown:
     - fuel_costs        # Per country
     - toll_costs        # Per country
     - driver_costs
     - overhead_costs
     - timeline_event_costs
   ```

2. Calculation Sources:
   - Fuel rates from Transport
   - Toll class from Transport
   - Driver rate from Transport
   - Business overheads from BusinessEntity

### Phase 4: Offer Generation

#### Business Requirements
1. Basic Offer:
   - Use route costs
   - Apply margin
   - Generate offer

2. AI Enhancement:
   - Generate fun fact
   - Enhance content
   - Save complete offer

#### Technical Implementation
1. Entities Used:
   ```python
   Offer:
     - route_id
     - cost_breakdown_id
     - margin_percentage
     - final_price
     - ai_content
     - fun_fact
   ```

2. Process Flow:
   - Calculate final price
   - Get AI enhancement
   - Store complete offer

## 3. PoC Limitations & Simplifications

### Fixed Values
- Empty driving: 200km/4h
- Event duration: 1h
- One rest event per route
- All routes feasible
- All compliance checks pass

### Disabled Features
- Route optimization
- Alternative routes
- Cost settings revision
- Advanced validations

### Simplified Elements
- Basic cost settings
- Static business entity
- Minimal error handling
- Simple data persistence

## 4. Cost Component Details

### Vehicle-Related Costs
- Fuel consumption (empty vs. loaded)
- Toll charges by country
- Basic maintenance rates

### Driver-Related Costs
- Daily rate from transport type
- Rest period costs
- Basic compliance costs

### Business Costs
- Overhead allocation
- Administrative costs
- Basic certifications

### Timeline Event Costs
- Loading/unloading charges
- Rest period expenses
- Basic handling costs

## 5. Technical Success Criteria

### Required Functionality
- Complete flow execution
- Accurate calculations
- Data persistence
- Basic error handling

### Implementation Standards
- Clean architecture
- Domain model alignment
- Service layer separation
- Proper entity relationships

### Performance Requirements
- Basic response times
- Simple caching
- Minimal database load

## 6. Future Evolution Path

### Potential Extensions
- Dynamic empty driving
- Multiple rest events
- Real compliance checks
- Advanced cost configurations

### Not In Scope
- Fleet management
- Real-time tracking
- Complex optimization
- Advanced reporting