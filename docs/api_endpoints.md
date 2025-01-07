# LoadApp.AI PoC - API Documentation

This document provides an overview of the primary API endpoints in the LoadApp.AI Proof of Concept (PoC). It is organized by resource category:

1. Cargo
2. Route
3. Cost
4. Offer
5. Transport
6. Business Routes
7. Location

Each section lists the available endpoints with request/response examples, parameters, and relevant error codes. Domain-level validations and constraints have been included based on the recently provided domain entity definitions and services.

---

## Global Domain Constraints & Notes

1. Many entity fields use Pydantic validations (e.g., weight and volume > 0).
2. Certain statuses are restricted, such as:
   - Cargo status: "pending", "in_transit", "delivered", "cancelled".
   - Route status: "draft", "planned", "in_progress", "completed", "cancelled".
   - Offer status: "draft", "finalized" (and intermediate statuses, if introduced).
3. Business entities must be "active" to create or update related resources (cargo, routes, etc.).
4. For the PoC, advanced validations (e.g., full certification checks) are mocked or always return True, but the structure is in place for future expansions.

---

## 1. Cargo Endpoints

File Reference: backend/api/routes/cargo_routes.py

Cargo endpoints handle creation, retrieval, updating, and deletion of cargo records, as well as status history.

### 1.1 Create Cargo

• URL: `/api/cargo`  
• Method: **POST**  
• Description: Creates a new cargo entry.

#### Request Headers
- Content-Type: application/json  
- Authorization: Bearer <token> (if authentication is enforced; PoC can be simplified)

#### Request Body (JSON)
Example:
```json
{
  "business_entity_id": "uuid-string",
  "weight": 1000.5,
  "volume": 35.2,
  "cargo_type": "flatbed",
  "value": "15000.00",
  "special_requirements": ["fragile", "insured"]
}
```
Field Details:
- business_entity_id (UUID, required): The ID of the associated business entity.
- weight (float, required, must be > 0): Weight of the cargo.
- volume (float, required, must be > 0): Volume of the cargo.
- cargo_type (string, required): E.g., "flatbed", "livestock", etc.
- value (decimal/string, required, must be > 0): Monetary value of the cargo.
- special_requirements (array of strings, optional): Special handling requirements.

#### Response Body (JSON)
On success (HTTP 201):
```json
{
  "id": "uuid-string",
  "business_entity_id": "uuid-string",
  "weight": 1000.5,
  "volume": 35.2,
  "cargo_type": "flatbed",
  "value": "15000.00",
  "special_requirements": ["fragile", "insured"],
  "status": "pending",
  "created_at": "2025-01-02T15:04:05Z",
  "updated_at": "2025-01-02T15:04:05Z"
}
```
- status is initially "pending"
- timestamps are in ISO-8601 format with UTC timezone

#### Error Responses
- 400 Bad Request: Invalid input format, missing fields, or invalid values (weight/volume/value <= 0)
- 404 Not Found: Business entity not found
- 409 Conflict: Business entity is not active
- 500 Internal Server Error: Database or unexpected error

---

### 1.2 Get Cargo

• URL: `/api/cargo/<cargo_id>`  
• Method: **GET**  
• Description: Retrieves details for a single cargo record.

#### Path Parameters
- cargo_id (UUID, required): The unique identifier for the cargo.

#### Response Body (JSON)
```json
{
  "id": "uuid-string",
  "business_entity_id": "uuid-string",
  "weight": 1000.5,
  "volume": 35.2,
  "cargo_type": "flatbed",
  "value": "15000.00",
  "special_requirements": [],
  "status": "pending",
  "created_at": "2025-01-02T15:04:05Z",
  "updated_at": "2025-01-02T15:04:05Z"
}
```

#### Error Responses
- 400 Bad Request: Invalid UUID format
- 404 Not Found: Cargo not found
- 500 Internal Server Error: Unexpected error

---

### 1.3 List Cargo

• URL: `/api/cargo`  
• Method: **GET**  
• Description: Retrieves a paginated list of cargo records.

#### Query Parameters
- page (int, optional): Defaults to 1
- size (int, optional): Defaults to 10. Max 100
- business_entity_id (UUID, optional): Filters cargo by business entity

#### Example Response (JSON)
```json
{
  "items": [
    {
      "id": "uuid-string",
      "business_entity_id": "uuid-string",
      "weight": 1000.5,
      "volume": 35.2,
      "cargo_type": "flatbed",
      "value": "15000.00",
      "special_requirements": [],
      "status": "pending",
      "created_at": "2025-01-02T15:04:05Z",
      "updated_at": "2025-01-02T15:04:05Z"
    }
    // ...
  ],
  "total": 50,
  "page": 1,
  "size": 10,
  "pages": 5
}
```

#### Error Responses
- 400 Bad Request: Invalid query parameters
- 500 Internal Server Error: Unexpected error

---

### 1.4 Update Cargo

• URL: `/api/cargo/<cargo_id>`  
• Method: **PUT**  
• Description: Updates cargo details.  
• Notes: Cannot update cargo if status is "in_transit", "delivered", or "cancelled"

#### Path Parameter
- cargo_id (UUID): The unique identifier for the cargo.

#### Request Body (JSON)
Example:
```json
{
  "weight": 1200,
  "volume": 40,
  "value": "16000.00",
  "status": "in_transit",
  "special_requirements": ["fragile"]
}
```
Fields are optional, but must meet the same constraints as creation.  
Status transitions must follow the valid state machine:
- pending → in_transit, cancelled
- in_transit → delivered, cancelled
- delivered → (no transitions, terminal state)
- cancelled → (no transitions, terminal state)

#### Response Body (JSON)
```json
{
  "id": "uuid-string",
  "business_entity_id": "uuid-string",
  "weight": 1200,
  "volume": 40,
  "cargo_type": "flatbed",
  "value": "16000.00",
  "special_requirements": ["fragile"],
  "status": "in_transit",
  "created_at": "2025-01-02T15:04:05Z",
  "updated_at": "2025-01-02T15:04:05Z"
}
```

#### Error Responses
- 400 Bad Request: Invalid data, forbidden status transition, or invalid values
- 404 Not Found: Cargo not found
- 409 Conflict: Cargo in terminal state or invalid status transition
- 500 Internal Server Error: Unexpected error

---

### 1.5 Delete Cargo

• URL: `/api/cargo/<cargo_id>`  
• Method: **DELETE**  
• Description: Soft-deletes a cargo entry.

#### Path Parameter
- cargo_id (UUID): The unique identifier for the cargo.

#### Response
- 204 No Content on successful deletion

#### Error Responses
- 400 Bad Request: Invalid cargo ID format
- 404 Not Found: Cargo not found
- 409 Conflict: Cargo is in transit and cannot be deleted
- 500 Internal Server Error

---

### 1.6 Get Cargo Status History

• URL: `/api/cargo/<cargo_id>/status-history`  
• Method: **GET**  
• Description: Retrieves the cargo's status change history.

#### Response Body (JSON) Example
```json
{
  "cargo_id": "uuid-string",
  "current_status": "in_transit",
  "history": [
    {
      "id": "uuid-string",
      "old_status": "pending",
      "new_status": "in_transit",
      "trigger": "offer_finalization",
      "trigger_id": "uuid-string",
      "details": {
        "timestamp": "2025-01-02T15:04:05Z",
        "trigger": "offer_finalization",
        "trigger_id": "uuid-string"
      }
    }
  ]
}
```

#### Error Responses
- 400 Bad Request: Invalid cargo ID format
- 404 Not Found: Cargo not found
- 500 Internal Server Error: Unexpected error

---

## 2. Route Endpoints

File Reference: backend/api/routes/route_routes.py

### 2.1 Calculate Route

• URL: `/api/route/calculate`  
• Method: **POST**  
• Description: Creates and calculates a new route, including compliance checks and route segments.

#### Request Body (JSON)
```json
{
  "transport_id": "uuid-string",
  "cargo_id": "uuid-string",
  "origin_id": "uuid-string",
  "destination_id": "uuid-string",
  "pickup_time": "2025-01-02T10:00:00Z",
  "delivery_time": "2025-01-03T15:00:00Z"
}
```
- transport_id (UUID): The transport to use.  
- cargo_id (UUID): The cargo to attach.  
- origin_id, destination_id (UUIDs): Location IDs.  
- pickup_time, delivery_time: ISO-8601 format, must be valid (delivery > pickup).

#### Sample Successful Response
```json
{
  "route": {
    "id": "uuid-string",
    "transport_id": "uuid-string",
    "cargo_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "origin_id": "uuid-string",
    "destination_id": "uuid-string",
    "pickup_time": "2025-01-02T10:00:00Z",
    "delivery_time": "2025-01-03T15:00:00Z",
    "empty_driving_id": "uuid-string",
    "timeline_events": [
      {
        "id": "uuid-string",
        "type": "pickup",
        "location": { /* location details */ },
        "planned_time": "2025-01-02T10:00:00Z",
        "duration_hours": 1,
        "event_order": 0
      },
      // ...
    ],
    "country_segments": [
      {
        "country_code": "DE",
        "distance_km": 300,
        "duration_hours": 5,
        "start_location": { /* location */ },
        "end_location": { /* location */ }
      }
    ],
    "total_distance_km": 500,
    "total_duration_hours": 9,
    "is_feasible": true,
    "status": "NEW",
    "validations": {
      "certifications_validated": true,
      "operating_countries_validated": true,
      "validation_timestamp": "2025-01-02T09:00:00Z",
      "validation_details": { /* mock data */ }
    }
  }
}
```

#### Error Responses
- 400 Bad Request: Invalid date format, or delivery_time <= pickup_time.  
- 404 Not Found: Transport or cargo not found.  
- 500 Internal Server Error: Failed route creation.

---

### 2.2 Check Route Feasibility

• URL: `/api/route/check-feasibility`  
• Method: **POST**  
• Description: Returns a simple feasibility check (PoC always returns feasible).

#### Example Response
```json
{
  "is_feasible": true,
  "validation_details": {
    "transport_valid": true,
    "cargo_valid": true,
    "timeline_valid": true,
    "distance_valid": true
  }
}
```

---

### 2.3 Get Route Timeline

• URL: `/api/route/<route_id>/timeline`  
• Method: **GET**  
• Description: Retrieves the timeline events for a specified route.

#### Sample Response
```json
{
  "timeline_events": [
    {
      "id": "uuid-string",
      "type": "pickup",
      "location": {
        "id": "uuid-string",
        "latitude": 51.0,
        "longitude": 9.0,
        "address": "Example Address"
      },
      "planned_time": "2025-01-02T10:00:00Z",
      "duration_hours": 1,
      "event_order": 0
    }
    // ...
  ]
}
```

---

### 2.4 Get Route Segments

• URL: `/api/route/<route_id>/segments`  
• Method: **GET**  
• Description: Retrieves country-wise route segments.

#### Sample Response
```json
{
  "segments": [
    {
      "country_code": "DE",
      "distance_km": 300,
      "duration_hours": 5,
      "start_location": { /* location */ },
      "end_location": { /* location */ }
    }
  ]
}
```

---

### 2.5 Update Route Timeline

• URL: `/api/route/<route_id>/timeline`  
• Method: **PUT**  
• Description: Updates the timeline events for a route.

#### Request Body
```json
{
  "timeline_events": [
    {
      "location_id": "uuid-string",
      "type": "pickup",
      "planned_time": "2025-01-02T10:00:00Z",
      "duration_hours": 1,
      "event_order": 0
    }
    // ...
  ]
}
```

#### Response Body
```json
{
  "timeline_events": [
    {
      "id": "uuid-string",
      "type": "pickup",
      "location": { /* location */ },
      "planned_time": "2025-01-02T10:00:00Z",
      "duration_hours": 1,
      "event_order": 0
    }
  ]
}
```
---

### 2.6 Get Route Status History

• URL: `/api/route/<route_id>/status-history`  
• Method: **GET**  
• Description: Retrieves status history for a given route, listing all recorded changes.

#### Example Response
```json
{
  "status_history": [
    {
      "id": "uuid-string",
      "status": "NEW",
      "comment": "Initial state",
      "timestamp": "2025-01-02T10:00:00Z"
    }
  ]
}
```
---

### 2.7 Update Route Status

• URL: `/api/route/<route_id>/status`  
• Method: **PUT**  
• Description: Updates the route's status and creates a history record.

#### Request Body
```json
{
  "status": "IN_PROGRESS",
  "comment": "Route started"
}
```

#### Response
```json
{
  "message": "Route status updated successfully",
  "old_status": "NEW",
  "new_status": "IN_PROGRESS"
}
```
---

## 3. Cost Endpoints

File Reference: backend/api/routes/cost_routes.py

These endpoints manage cost settings and cost breakdowns for routes.

### 3.1 Create Cost Settings

• URL: `/api/cost/settings/<route_id>`  
• Method: **POST**  
• Description: Creates cost settings for the specified route 

#### Request Body
```json
{
    "enabled_components": ["fuel", "driver", "toll"],
    "rates": {
        "fuel_rate": "2.50",
        "fuel_surcharge_rate": "0.15",
        "toll_rate": "0.25",
        "driver_base_rate": "200.00",
        "driver_time_rate": "25.00",
        "event_rate": "50.00"
    }
}
```

#### Response
```json
{
    "id": "uuid",
    "route_id": "uuid",
    "enabled_components": ["fuel", "driver", "toll"],
    "rates": {
        "fuel_rate": "2.50",
        "fuel_surcharge_rate": "0.15",
        "toll_rate": "0.25",
        "driver_base_rate": "200.00",
        "driver_time_rate": "25.00",
        "event_rate": "50.00"
    }
}
```

#### Validation Rules
- At least one component must be enabled
- Rate values must be within allowed ranges:
  - `fuel_rate`: 0.50 - 5.00 EUR/L (country-specific)
  - `fuel_surcharge_rate`: 0.01 - 0.50 (percentage, country-specific)
  - `toll_rate`: 0.10 - 2.00 EUR/km (country-specific)
  - `driver_base_rate`: 100.00 - 500.00 EUR/day
  - `driver_time_rate`: 10.00 - 100.00 EUR/hour (country-specific)
  - `event_rate`: 20.00 - 200.00 EUR/event

#### Error Responses
- 400 Bad Request: Invalid input data or validation failure
- 404 Not Found: Route not found
- 500 Internal Server Error: Unexpected error

---

### 3.2 Update Cost Settings

• URL: `/api/cost/settings/<route_id>`  
• Method: **PUT**  
• Description: Updates existing cost settings.

#### Request Body
```json
{
    "enabled_components": ["fuel", "driver", "overhead"],
    "rates": {
        "fuel_rate": "1.6"
    }
}
```

#### Response
```json
{
    "id": "uuid",
    "route_id": "uuid",
    "enabled_components": ["fuel", "driver", "overhead"],
    "rates": {
        "fuel_rate": "1.6",
        "driver_base_rate": "200.00"
    }
}
```

#### Validation Rules
- At least one component must be enabled if updating components
- Rate values must be within allowed ranges (same as create endpoint)
- Only modified rates need to be included in request

#### Error Responses
- 400 Bad Request:
  ```json
  {
      "error": "Invalid rates: fuel_rate value 10.0 outside allowed range (0.50 - 5.00)"
  }
  ```
- 404 Not Found: Route or settings not found
  ```json
  {
      "error": "Cost settings not found for route"
  }
  ```
- 500 Internal Server Error: Unexpected error

---

### 3.3 Get Fuel Rates

• URL: `/api/cost/rates/fuel/<route_id>`  
• Method: **GET**  
• Description: Get default and current fuel rates for countries in a route.

#### Response
```json
{
    "default_rates": {
        "DE": "1.85",
        "PL": "1.65"
    },
    "current_settings": {
        "fuel_rate_DE": "1.90",
        "fuel_rate_PL": "1.70"
    },
    "consumption_rates": {
        "empty": "0.22",
        "loaded": "0.29",
        "per_ton": "0.03"
    }
}
```

#### Error Responses
- 404 Not Found: Route not found
- 500 Internal Server Error: Unexpected error

---

### 3.4 Get Toll Rates

• URL: `/api/cost/rates/toll/<route_id>`  
• Method: **GET**  
• Description: Get default toll rates and adjustments based on vehicle classification for countries in a route.

#### Response
```json
{
    "default_rates": {
        "DE": {
            "toll_class_rates": {
                "1": "0.167",
                "2": "0.188",
                "3": "0.208",
                "4": "0.228"
            },
            "euro_class_adjustments": {
                "VI": "0.000",
                "V": "0.021",
                "IV": "0.042",
                "III": "0.063"
            }
        },
        "PL": {
            "toll_class_rates": {
                "1": "0.167",
                "2": "0.188",
                "3": "0.208",
                "4": "0.228"
            },
            "euro_class_adjustments": {
                "VI": "0.000",
                "V": "0.021",
                "IV": "0.042",
                "III": "0.063"
            }
        }
    },
    "current_settings": {
        "toll_rate_DE": "0.20",
        "toll_rate_PL": "0.25"
    },
    "business_overrides": {
        "DE": {
            "rate_multiplier": "1.2",
            "reason": "High traffic zone"
        }
    }
}
```

#### Error Responses
- 404 Not Found: Route not found
- 500 Internal Server Error: Unexpected error

---

### 3.5 Get Event Rates

• URL: `/api/cost/rates/event`  
• Method: **GET**  
• Description: Get default event rates and their allowed ranges.

#### Response
```json
{
    "rates": {
        "pickup": "50.00",
        "delivery": "50.00",
        "rest": "30.00"
    },
    "ranges": {
        "pickup": ["20.00", "200.00"],
        "delivery": ["20.00", "200.00"],
        "rest": ["20.00", "150.00"]
    }
}
```

#### Error Responses
- 500 Internal Server Error: Unexpected error

---

### 3.6 Clone Cost Settings

• URL: `/api/cost/settings/<target_route_id>/clone`  
• Method: **POST**  
• Description: Clone cost settings from one route to another.

#### Request Body
```json
{
    "source_route_id": "uuid-string",
    "rate_modifications": {
        "fuel_rate_DE": "1.90",
        "toll_rate_PL": "0.25"
    }
}
```

#### Response
```json
{
    "id": "uuid",
    "route_id": "uuid",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
        "fuel_rate_DE": "1.90",
        "fuel_rate_PL": "1.65",
        "toll_rate_DE": "0.20",
        "toll_rate_PL": "0.25",
        "driver_base_rate": "200.00"
    }
}
```

#### Error Responses
- 404 Not Found: Source route or target route not found
- 400 Bad Request: Invalid rate modifications
- 500 Internal Server Error: Unexpected error

---

### 3.7 Patch Cost Settings

• URL: `/api/cost/settings/<route_id>`  
• Method: **PATCH**  
• Description: Partially update cost settings.

#### Request Body
```json
{
    "rates": {
        "fuel_rate_DE": "1.90"
    }
}
```

#### Response
```json
{
    "id": "uuid",
    "route_id": "uuid",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
        "fuel_rate_DE": "1.90",
        "fuel_rate_PL": "1.65",
        "toll_rate_DE": "0.20",
        "driver_base_rate": "200.00"
    }
}
```

#### Error Responses
- 404 Not Found: Cost settings not found
- 400 Bad Request: Invalid rate values
- 500 Internal Server Error: Unexpected error

---

### 3.8 Get Cost Settings

• URL: `/api/cost/settings/<route_id>`  
• Method: **GET**  
• Description: Fetches the current cost settings for the given route.

#### Response
```json
{
    "id": "uuid-string",
    "route_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
        "fuel_rate": "1.6",
        "toll_rate": "0.2"
    }
}
```

#### Error Responses
- 404 Not Found: Route or settings not found
- 500 Internal Server Error: Unexpected error

---

### 3.9 Calculate Costs

• URL: `/api/cost/calculate/<route_id>`  
• Method: **POST**  
• Description: Performs a cost calculation for the given route based on current cost settings.

#### Response
```json
{
    "breakdown": {
        "id": "uuid-string",
        "route_id": "uuid-string",
        "fuel_costs": {
            "DE": "150.00"
        },
        "toll_costs": {
            "DE": "60.00"
        },
        "driver_costs": "120.00",
        "overhead_costs": "80.00",
        "timeline_event_costs": {
            "pickup": "40.00"
        },
        "total_cost": "450.00"
    }
}
```

#### Error Responses
- 404 Not Found: Route not found or cost settings not found
- 500 Internal Server Error: Unexpected error

---

### 3.10 Get Cost Breakdown

• URL: `/api/cost/breakdown/<route_id>`  
• Method: **GET**  
• Description: Retrieves the saved cost breakdown for the specified route.

#### Response
```json
{
    "breakdown": {
        "id": "uuid-string",
        "route_id": "uuid-string",
        "fuel_costs": {
            "DE": "150.00"
        },
        "toll_costs": { "DE": "60.00" },
        "driver_costs": "120.00",
        "overhead_costs": "80.00",
        "timeline_event_costs": {
            "pickup": "40.00"
        },
        "total_cost": "450.00"
    }
}
```

#### Error Responses
- 404 Not Found: Route not found or cost breakdown not found
- 500 Internal Server Error: Unexpected error

---

## 4. Offer Endpoints

File Reference: backend/api/routes/offer_routes.py

### 4.1 Generate an Offer

• URL: `/api/offer/generate/<route_id>`  
• Method: **POST**  
• Description: Creates an offer using the route's cost breakdown, applying a margin. Optionally uses AI to enhance content.

#### Request Body
```json
{
  "margin_percentage": "15.0",
  "enhance_with_ai": true
}
```

#### Sample Response
```json
{
  "offer": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "cost_breakdown_id": "uuid-string",
    "margin_percentage": "15.0",
    "final_price": "517.50",
    "ai_content": "Enhanced pitch text",
    "fun_fact": "AI-generated fun fact",
    "created_at": "2025-01-01T10:00:00Z"
  }
}
```
---

### 4.2 Enhance an Existing Offer

• URL: `/api/offer/<offer_id>/enhance`  
• Method: **POST**  
• Description: Uses AI to add extra text/fun facts to an existing offer.

#### Response
```json
{
  "offer": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "status": "DRAFT",
    "ai_content": "Revised pitch text",
    "fun_fact": "Revised fun fact",
    "final_price": "517.50"
  }
}
```
---

### 4.3 Get an Offer

• URL: `/api/offer/<offer_id>`  
• Method: **GET**  
• Description: Retrieves offer details by offer ID.

#### Response
```json
{
  "offer": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "status": "DRAFT",
    "final_price": "517.50",
    "ai_content": "Some pitch text",
    "fun_fact": "Little known fact",
    "created_at": "2025-01-01T10:00:00Z"
  }
}
```
---

### 4.4 Finalize an Offer

• URL: `/api/offer/<offer_id>/finalize`  
• Method: **POST**  
• Description: Marks the offer as finalized, logs status changes, and can update route/cargo statuses if needed.

#### Sample Response
```json
{
  "status": "success",
  "message": "Offer finalized successfully",
  "offer": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "status": "FINALIZED",
    "final_price": "517.50",
    "ai_content": "Enhanced pitch text",
    "fun_fact": "Even better fun fact",
    "created_at": "2025-01-01T10:00:00Z",
    "finalized_at": "2025-01-02T09:00:00Z"
  }
}
```
---

### 4.5 Get Offer Status History

• URL: `/api/offer/<offer_id>/status-history`  
• Method: **GET**  
• Description: Returns the status changes recorded for the specified offer.

#### Example Response
```json
[
  {
    "id": "uuid-string",
    "status": "DRAFT",
    "timestamp": "2025-01-01T10:00:00Z",
    "comment": "Initial creation"
  },
  {
    "id": "uuid-string",
    "status": "FINALIZED",
    "timestamp": "2025-01-02T09:00:00Z"
  }
]
```
---

### 4.6 Update Offer Status

• URL: `/api/offer/<offer_id>/status`  
• Method: **PUT**  
• Description: Manually updates the status of an offer (e.g., from "DRAFT" to "FINALIZED").

#### Request Body
```json
{
  "status": "FINALIZED",
  "comment": "Approved by manager"
}
```

#### Response
```json
{
  "message": "Offer status updated successfully",
  "old_status": "DRAFT",
  "new_status": "FINALIZED"
}
```
---

## 5. Transport Endpoints

File Reference: backend/api/routes/transport_routes.py

### 5.1 List Transport Types

• URL: `/api/transport/types`  
• Method: **GET**  
• Description: Lists all available transport types.

#### Example Response
```json
[
  {
    "id": "uuid-string",
    "name": "Flatbed",
    "truck_specifications": {
      "fuel_consumption_empty": 0.22,
      "fuel_consumption_loaded": 0.29,
      "toll_class": "Class B",
      "euro_class": "Euro VI",
      "co2_class": "Low",
      "maintenance_rate_per_km": 0.1
    },
    "driver_specifications": {
      "daily_rate": 138.0,
      "required_license_type": "C+E",
      "required_certifications": ["ADR"]
    }
  }
]
```
---

### 5.2 Get a Transport Type by ID

• URL: `/api/transport/types/<type_id>`  
• Method: **GET**  
• Description: Retrieves a single transport type's details by ID.

#### Response
```json
{
  "id": "uuid-string",
  "name": "Flatbed",
  "truck_specifications": { /* ... */ },
  "driver_specifications": { /* ... */ }
}
```
---

### 5.3 List Business Transports

• URL: `/api/transport/business/<business_id>/transports`  
• Method: **GET**  
• Description: Lists all transports associated with a specific business entity.

#### Response
```json
[
  {
    "id": "uuid-string",
    "transport_type_id": "flatbed",
    "business_entity_id": "uuid-string",
    "truck_specifications": {
      "fuel_consumption_empty": 0.22,
      "fuel_consumption_loaded": 0.29,
      "toll_class": "4-axle",
      "euro_class": "EURO6",
      "co2_class": "A",
      "maintenance_rate_per_km": "0.15"
    },
    "driver_specifications": {
      "daily_rate": "138.00",
      "driving_time_rate": "35.00",
      "required_license_type": "CE",
      "required_certifications": ["ADR"]
    },
    "is_active": true
  }
]
```

#### Error Responses
- 400 Bad Request: Invalid business ID format
- 500 Internal Server Error: Unexpected error

---

### 5.4 Create Transport

• URL: `/api/transport`  
• Method: **POST**  
• Description: Creates a new transport for a business entity.

#### Request Body
```json
{
  "transport_type_id": "flatbed",
  "business_entity_id": "uuid-string"
}
```

#### Response
```json
{
  "id": "uuid-string",
  "transport_type_id": "flatbed",
  "business_entity_id": "uuid-string",
  "truck_specifications": { /* ... */ },
  "driver_specifications": { /* ... */ },
  "is_active": true
}
```

#### Error Responses
- 400 Bad Request: Missing required fields or invalid format
- 500 Internal Server Error: Unexpected error

---

### 5.5 Get Transport

• URL: `/api/transport/<transport_id>`  
• Method: **GET**  
• Description: Retrieves details of a specific transport.

#### Response
```json
{
  "id": "uuid-string",
  "transport_type_id": "flatbed",
  "business_entity_id": "uuid-string",
  "truck_specifications": { /* ... */ },
  "driver_specifications": { /* ... */ },
  "is_active": true
}
```

#### Error Responses
- 400 Bad Request: Invalid transport ID format
- 404 Not Found: Transport not found
- 500 Internal Server Error: Unexpected error

---

### 5.6 Deactivate Transport

• URL: `/api/transport/<transport_id>/deactivate`  
• Method: **POST**  
• Description: Deactivates a transport, making it unavailable for new routes.

#### Response
```json
{
  "message": "Transport deactivated successfully",
  "transport": {
    "id": "uuid-string",
    "transport_type_id": "flatbed",
    "business_entity_id": "uuid-string",
    "truck_specifications": { /* ... */ },
    "driver_specifications": { /* ... */ },
    "is_active": false
  }
}
```

#### Error Responses
- 400 Bad Request: Invalid transport ID format
- 404 Not Found: Transport not found
- 500 Internal Server Error: Unexpected error

---

### 5.7 Reactivate Transport

• URL: `/api/transport/<transport_id>/reactivate`  
• Method: **POST**  
• Description: Reactivates a previously deactivated transport.

#### Response
```json
{
  "message": "Transport reactivated successfully",
  "transport": {
    "id": "uuid-string",
    "transport_type_id": "flatbed",
    "business_entity_id": "uuid-string",
    "truck_specifications": { /* ... */ },
    "driver_specifications": { /* ... */ },
    "is_active": true
  }
}
```

#### Error Responses
- 400 Bad Request: Invalid transport ID format
- 404 Not Found: Transport not found
- 500 Internal Server Error: Unexpected error

---

## 6. Business Routes

**Note: Most business routes are not implemented in PoC. Only listing active businesses is available.**

File Reference: backend/api/routes/business_routes.py

### 6.1 List Active Businesses

• URL: `/api/business`  
• Method: **GET**  
• Description: Lists all active business entities.

#### Response
```json
[
  {
    "id": "uuid-string",
    "name": "Active Transport Company",
    "address": "123 Main St",
    "contact_info": {
      "email": "active@test.com"
    },
    "business_type": "carrier",
    "certifications": ["ISO9001"],
    "operating_countries": ["DE", "PL"],
    "cost_overheads": {
      "admin": "100.00"
    },
    "is_active": true
  }
]
```

#### Error Responses
- 500 Internal Server Error: Database error occurred

### 6.2 Other Business Routes (Not Implemented in PoC)

The following endpoints return 501 Not Implemented:

1. Create Business Entity
   • URL: `/api/business`  
   • Method: **POST**

2. Get Business Entity
   • URL: `/api/business/<business_id>`  
   • Method: **GET**

3. Update Business Entity
   • URL: `/api/business/<business_id>`  
   • Method: **PUT**

4. Validate Business Entity
   • URL: `/api/business/<business_id>/validate`  
   • Method: **POST**

These endpoints are planned for future implementation beyond the PoC phase.

## Common Error Handling & Response Structure

All endpoints may return:
- **400 Bad Request**: Invalid input data or parameters.  
- **401 Unauthorized**: Authentication required (if PoC enforces).  
- **404 Not Found**: Requested resource not found.  
- **409 Conflict**: Conflicting state changes.  
- **500 Internal Server Error**: Unexpected server-side failure.

Most error responses adhere to a standard format:
```json
{
  "error": "Detailed error message"
}
```

## Authentication (PoC Simplification)

Authentication may be relaxed in a PoC, but if enabled, it typically uses a Bearer token:
```
Authorization: Bearer <your_token_here>
```
---

## 7. Location Endpoints

File Reference: backend/api/routes/location_routes.py

Location endpoints handle creation, validation, and retrieval of location records.

### 7.1 Create Location

• URL: `/api/location`  
• Method: **POST**  
• Description: Creates a new location entry with geocoding.

#### Request Headers
- Content-Type: application/json

#### Request Body (JSON)
Example:
```json
{
  "address": "Berlin, Germany"
}
```
Field Details:
- address (string, required): The full address to geocode

#### Response Body (JSON)
On success (HTTP 201):
```json
{
  "id": "uuid-string",
  "address": "Berlin, Germany",
  "latitude": 52.520008,
  "longitude": 13.404954
}
```

#### Error Responses
- 400 Bad Request: Missing address or invalid format
- 500 Internal Server Error: Geocoding failed or other server error

---

### 7.2 Get Location

• URL: `/api/location/<location_id>`  
• Method: **GET**  
• Description: Retrieves details for a single location.

#### Path Parameters
- location_id (UUID, required): The unique identifier for the location.

#### Response Body (JSON)
```json
{
  "id": "uuid-string",
  "address": "Berlin, Germany",
  "latitude": 52.520008,
  "longitude": 13.404954
}
```

#### Error Responses
- 400 Bad Request: Invalid UUID format
- 404 Not Found: Location not found
- 500 Internal Server Error: Unexpected error

---

### 7.3 Validate Location

• URL: `/api/location/validate`  
• Method: **POST**  
• Description: Validates an address by attempting to geocode it.

#### Request Body (JSON)
```json
{
  "address": "Berlin, Germany"
}
```

#### Response Body (JSON)
```json
{
  "valid": true,
  "error": null
}
```
or if invalid:
```json
{
  "valid": false,
  "error": "Could not geocode address"
}
```

#### Error Responses
- 400 Bad Request: Missing address
- 200 OK with validation result (even if address is invalid)

---

# End of File 