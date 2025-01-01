# LoadApp.AI Product Requirements Document
Version: Final PoC
Last Updated: December 28, 2024

## 1. Overview

LoadApp.AI enables transport managers to efficiently plan routes, calculate costs, and generate offers. This document maps business requirements to technical implementation for the PoC version.

## FILES TO REFERENCE:

g_docs/business_req.md
g_docs/domain_layer_cons.md

## PROJECT STRUCTURE:

.
├── README.md
├── alembic.ini
├── backend
│   ├── __init__.py
│   ├── api
│   │   └── routes
│   │       ├── route_routes.py
│   │       └── transport_routes.py
│   ├── app.py
│   ├── config.py
│   ├── domain
│   │   ├── __init__.py
│   │   ├── entities
│   │   │   ├── __init__.py
│   │   │   ├── business.py
│   │   │   ├── cargo.py
│   │   │   ├── location.py
│   │   │   ├── route.py
│   │   │   └── transport.py
│   │   └── services
│   │       ├── cost_service.py
│   │       ├── offer_service.py
│   │       ├── route_service.py
│   │       └── transport_service.py
│   └── infrastructure
│       ├── __init__.py
│       ├── adapters
│       │   ├── google_maps_adapter.py
│       │   ├── openai_adapter.py
│       │   └── toll_rate_adapter.py
│       ├── container.py
│       ├── database.py
│       ├── external_services
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── google_maps_service.py
│       │   ├── openai_service.py
│       │   └── toll_rate_service.py
│       ├── logging.py
│       ├── models
│       │   ├── business_models.py
│       │   ├── cargo_models.py
│       │   ├── route_models.py
│       │   └── transport_models.py
│       └── repositories
│           ├── base.py
│           ├── business_repository.py
│           ├── cargo_repository.py
│           ├── location_repository.py
│           ├── route_repository.py
│           └── transport_repository.py
├── docs
│   └── TESTING_SETUP.MD
├── frontend
│   ├── __init__.py
│   └── streamlit_app.py
├── g_docs
│   ├── business_req.md
│   ├── domain_layer_cons.md
│   ├── implementation_gameplan.md
│   ├── implementation_guidelines.md
│   ├── prd.md
│   └── testing_requirements.md
├── k_docs
├── loadapp.db
├── migrations
│   ├── __init__.py
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 20241231_1618_707351151d52_initial_schema.py
│       └── 20241231_1643_19e0a6c12b96_add_route_status.py
├── pytest.ini
├── requirements.txt
├── scripts
│   ├── init_db.py
│   ├── run_tests.sh
│   ├── start_backend.sh
│   └── start_frontend.sh
├── temp
│   ├── google_maps_service.py
│   ├── openai_service.py
│   └── toll_rate_service.py
├── template.env
├── test.db
└── tests
    ├── __init__.py
    ├── backend
    │   ├── __init__.py
    │   ├── api
    │   │   └── routes
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
    │   │       ├── test_cost_service.py
    │   │       ├── test_offer_service.py
    │   │       ├── test_route_service.py
    │   │       └── test_transport_service.py
    │   ├── external_services
    │   │   ├── conftest.py
    │   │   ├── test_google_maps_service.py
    │   │   ├── test_openai_service.py
    │   │   └── test_toll_rate_service.py
    │   ├── infrastructure
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
    │   └── test_app.py
    ├── conftest.py
    ├── conftest_old.py
    └── frontend
        ├── __init__.py
        └── test_streamlit_app.py



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
1. Compliance Check:
   - Validate truck/driver for transport type
   - Check business entity paperwork
   - PoC: Always returns true

2. Route Generation:
   - Add empty driving (200km/4h)
   - Calculate main route
   - Create timeline events
   - Generate country segments

3. Display Requirements:
   - Map visualization
   - Timeline display
   - Total distance/duration
   - Feasibility status

#### Technical Implementation
1. Entities Used:
   ```python
   Route:
     - transport_id       # Links to Transport
     - empty_driving     # Fixed 200km/4h
     - timeline_events   # Pickup, rest, delivery
     - country_segments  # For cost calculations
     - is_feasible      # Always true

   TimelineEvent:
     - type             # pickup/rest/delivery
     - duration_hours   # Fixed 1h
     - location
     - event_order

   CountrySegment:
     - country_code
     - distance_km
     - duration_hours
   ```

2. Fixed Values:
   - Empty driving: 200km/4h
   - Event duration: 1h each
   - One rest event in middle
   - All routes feasible

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