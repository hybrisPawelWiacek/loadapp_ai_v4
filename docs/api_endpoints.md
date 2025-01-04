# LoadApp.AI PoC - API Documentation

This document provides an overview of the primary API endpoints in the LoadApp.AI Proof of Concept (PoC). It is organized by resource category:

1. Cargo
2. Route
3. Cost
4. Offer
5. Transport

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
- weight (float, required, must be > 0).
- volume (float, required, must be > 0).
- cargo_type (string, required): E.g., "flatbed", "livestock", etc.
- value (decimal/string, required, must be > 0).
- special_requirements (array of strings, optional).

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
  "status": "pending"
}
```
- status is initially "pending."

#### Error Responses
- 400 Bad Request: Invalid input format or missing fields.  
- 404 Not Found: Business entity not found.  
- 409 Conflict: Business entity is not active.  
- 500 Internal Server Error: Database or unexpected error.

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
  "status": "pending"
}
```

#### Error Responses
- 400 Bad Request: Invalid UUID format.  
- 404 Not Found: Cargo not found.  
- 500 Internal Server Error: Unexpected error.

---

### 1.3 List Cargo

• URL: `/api/cargo`  
• Method: **GET**  
• Description: Retrieves a paginated list of cargo records.

#### Query Parameters
- page (int, optional): Defaults to 1.  
- size (int, optional): Defaults to 10. Max 100.  
- business_entity_id (UUID, optional): Filters cargo by business entity.

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
      "status": "pending"
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
- 400 Bad Request: Invalid query parameters.  
- 500 Internal Server Error: Unexpected error.

---

### 1.4 Update Cargo

• URL: `/api/cargo/<cargo_id>`  
• Method: **PUT**  
• Description: Updates cargo details.  
• Notes: Cannot update cargo if status is "in_transit."

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
If updating status, the system checks if the transition is valid.

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
  "status": "in_transit"
}
```

#### Error Responses
- 400 Bad Request: Invalid data or forbidden status transition.  
- 404 Not Found: Cargo not found.  
- 409 Conflict: Cargo already in transit (or a conflicting update).  
- 500 Internal Server Error: Unexpected error.

---

### 1.5 Delete Cargo

• URL: `/api/cargo/<cargo_id>`  
• Method: **DELETE**  
• Description: Soft-deletes a cargo entry.

#### Path Parameter
- cargo_id (UUID): The unique identifier for the cargo.

#### Response
- 204 No Content on successful deletion.

#### Error Responses
- 400 Bad Request: Invalid cargo ID format.  
- 404 Not Found: Cargo not found.  
- 409 Conflict: Cargo is in transit and cannot be deleted.  
- 500 Internal Server Error.

---

### 1.6 Get Cargo Status History

• URL: `/api/cargo/<cargo_id>/status-history`  
• Method: **GET**  
• Description: Retrieves the cargo’s status change history.

#### Response Body (JSON) Example
```json
{
  "cargo_id": "uuid-string",
  "current_status": "pending",
  "history": [
    {
      "id": "uuid-string",
      "old_status": "pending",
      "new_status": "in_transit",
      "trigger": "manual_update",
      "details": { "updated_by": "api", "updated_fields": ["status"] },
      "timestamp": "2025-01-02T15:04:05Z"
    }
  ]
}
```
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
• Description: Updates the route’s status and creates a history record.

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
• Description: Creates cost settings for the specified route.

#### Request Body
```json
{
  "enabled_components": ["fuel", "toll", "driver"],
  "rates": {
    "fuel_rate": "1.5",
    "toll_rate": "0.2"
  }
}
```

#### Response
```json
{
  "settings": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
      "fuel_rate": "1.5",
      "toll_rate": "0.2"
    }
  }
}
```

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
  "settings": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "enabled_components": ["fuel", "driver", "overhead"],
    "rates": {
      "fuel_rate": "1.6"
    }
  }
}
```
---

### 3.3 Calculate Costs

• URL: `/api/cost/calculate/<route_id>`  
• Method: **POST**  
• Description: Performs a cost calculation for the given route based on current cost settings.

#### Sample Response
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
---

### 3.4 Get Cost Breakdown

• URL: `/api/cost/breakdown/<route_id>`  
• Method: **GET**  
• Description: Retrieves the saved cost breakdown for the specified route.

#### Sample Response
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
---

### 3.5 Get Cost Settings

• URL: `/api/cost/settings/<route_id>`  
• Method: **GET**  
• Description: Fetches the current cost settings for the given route.

#### Sample Response
```json
{
  "settings": {
    "id": "uuid-string",
    "route_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
      "fuel_rate": "1.6",
      "toll_rate": "0.2"
    }
  }
}
```
---

## Cost Settings Endpoints

### POST /api/cost/settings/{route_id}
Creates cost settings for a route with rate validation.

**Path Parameters:**
- `route_id`: UUID of the route

**Request Body:**
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

**Response:**
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

**Validation Rules:**
- `fuel_rate`: 0.50 - 5.00 EUR/L (country-specific)
- `fuel_surcharge_rate`: 0.01 - 0.50 (percentage, country-specific)
- `toll_rate`: 0.10 - 2.00 EUR/km (country-specific)
- `driver_base_rate`: 100.00 - 500.00 EUR/day
- `driver_time_rate`: 10.00 - 100.00 EUR/hour (country-specific)
- `event_rate`: 20.00 - 200.00 EUR/event

### POST /api/cost/settings/{target_route_id}/clone
Clones cost settings from one route to another with optional rate modifications.

**Path Parameters:**
- `target_route_id`: UUID of the target route

**Request Body:**
```json
{
    "source_route_id": "uuid",
    "rate_modifications": {
        "fuel_rate": "2.75",
        "driver_base_rate": "220.00"
    }
}
```

**Response:**
```json
{
    "settings": {
        "id": "uuid",
        "route_id": "uuid",
        "business_entity_id": "uuid",
        "enabled_components": ["fuel", "driver", "toll"],
        "rates": {
            "fuel_rate": "2.75",
            "driver_base_rate": "220.00",
            "toll_rate": "0.25",
            "event_rate": "50.00"
        }
    }
}
```

**Validation Rules:**
- Source and target routes must belong to the same business entity
- Source and target routes must have compatible transport types
- Rate modifications must pass the same validation rules as regular rates
- Rate values cannot be negative
- Only modified rates need to be included in rate_modifications
- Unmodified rates are copied as-is from source settings

**Error Responses:**
- 400 Bad Request:
  - Invalid rate modifications format
  - Invalid rate values
  - Negative rate values
  - Different business entities
  - Incompatible transport types
- 404 Not Found:
  - Source route not found
  - Target route not found
  - Transport information not found

### PATCH /api/cost/settings/{route_id}
Updates cost settings partially for a route.

**Path Parameters:**
- `route_id`: UUID of the route

**Request Body:**
```json
{
    "enabled_components": ["fuel", "toll", "driver"],  // Optional
    "rates": {                                        // Optional
        "fuel_rate": "2.50",
        "toll_rate": "0.25",
        "driver_base_rate": "200.00"
    }
}
```

**Validation Rules:**
- At least one component must be enabled if updating components
- Rate values must be within allowed ranges:
  - fuel_rate: 0.50 - 5.00 EUR/L
  - toll_rate: 0.10 - 2.00 EUR/km
  - driver_base_rate: 100.00 - 500.00 EUR/day
  - driver_time_rate: 10.00 - 100.00 EUR/hour
  - event_rate: 20.00 - 200.00 EUR/event

**Response:**
```json
{
    "id": "uuid-string",
    "route_id": "uuid-string",
    "business_entity_id": "uuid-string",
    "enabled_components": ["fuel", "toll", "driver"],
    "rates": {
        "fuel_rate": "2.50",
        "toll_rate": "0.25",
        "driver_base_rate": "200.00"
    }
}
```

**Error Responses:**
- 400 Bad Request: Invalid input data or validation failure
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
- 500 Internal Server Error: Unexpected server error

**Example Request:**
```bash
curl -X PATCH http://localhost:5001/api/cost/settings/123e4567-e89b-12d3-a456-426614174000 \
     -H "Content-Type: application/json" \
     -d '{
         "rates": {
             "fuel_rate": "2.75",
             "driver_base_rate": "220.00"
         }
     }'
```

## 4. Offer Endpoints

File Reference: backend/api/routes/offer_routes.py

### 4.1 Generate an Offer

• URL: `/api/offer/generate/<route_id>`  
• Method: **POST**  
• Description: Creates an offer using the route’s cost breakdown, applying a margin. Optionally uses AI to enhance content.

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
• Description: Retrieves a single transport type’s details by ID.

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

# End of File 