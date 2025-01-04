# Cargo API Implementation Gameplan
Version: 1.3
Last Updated: January 4, 2024

## Progress Status

### ✅ Completed Components

1. **Basic CRUD Implementation**
   - Created `cargo_routes.py` with all endpoints
   - Implemented request validation
   - Added error handling
   - Registered blueprint in main app

2. **Status Management**
   - Defined valid status transitions
   - Implemented status validation
   - Added terminal state handling
   - Enforced state transition rules

3. **Audit Logging**
   - Added structured logging with `structlog`
   - Implemented operation logging
   - Added error tracking
   - Included context in log messages

4. **Offer Integration**
   - Status transition rules ✅
   - Offer finalization trigger ✅
   - Route status synchronization ✅

5. **Business Entity Integration**
   - Basic existence check ✅
   - Active status validation ✅

### 🚧 In Progress

1. **Business Entity Advanced Validation**
   - Certification validation ⏳
   - Operating countries validation ⏳

### 📋 Next Steps

1. **Business Entity Validation Implementation**
   - Implement certification validation logic
   - Add operating countries validation
   - Update relevant test cases
   - Document validation rules

## Overview
This document outlines the implementation strategy for cargo-related endpoints in LoadApp.AI, with special focus on offer finalization and status management.

## 1. Status Management

### 1.1 Status Transitions
```python
VALID_STATUS_TRANSITIONS = {
    "pending": ["in_transit", "cancelled"],  # in_transit only after offer finalization
    "in_transit": ["delivered", "cancelled"],
    "delivered": [],  # Terminal state
    "cancelled": []   # Terminal state
}
```

### 1.2 Status Rules
1. Initial state is always `pending`
2. Can only transition to `in_transit` after offer finalization
3. Cannot modify cargo details in `in_transit` state
4. Terminal states (`delivered`, `cancelled`) cannot be changed

## 2. Required Endpoints

### 2.1 Core Endpoints ✅
```
POST /api/cargo
- Create new cargo entry ✅
- Required for route calculation phase ✅
- Associates cargo with business entity ✅

GET /api/cargo/{cargo_id}
- Retrieve cargo details ✅
- Used by route calculation and cost management ✅

PUT /api/cargo/{cargo_id}
- Update cargo details ✅
- Blocked when cargo is in_transit ✅

GET /api/cargo
- List cargo entries ✅
- Supports filtering by business entity ✅
- Pagination support ✅

DELETE /api/cargo/{cargo_id}
- Mark cargo as deleted ✅
- Blocked when cargo is in_transit ✅
```

### 2.2 New Integration Endpoints ⏳
```
POST /api/cargo/{cargo_id}/finalize-offer
- Handle offer finalization
- Transition cargo to in_transit
- Synchronize route status
- Validate business rules

GET /api/cargo/{cargo_id}/status-history
- Track status changes
- Include timestamps
- Record triggering events
```

### 2.3 Request/Response Structures ✅
```python
# Create/Update Cargo Request
{
    "business_entity_id": UUID,
    "weight": float,
    "volume": float,
    "cargo_type": str,  # general, temperature_controlled, hazardous, etc.
    "value": Decimal,
    "special_requirements": List[str],
    "status": str  # pending, in_transit, delivered, cancelled
}

# Cargo Response
{
    "id": UUID,
    "business_entity_id": UUID,
    "weight": float,
    "volume": float,
    "cargo_type": str,
    "value": str,  # Decimal as string
    "special_requirements": List[str],
    "status": str,
    "created_at": datetime,
    "updated_at": datetime
}

# List Cargo Response
{
    "items": List[CargoResponse],
    "total": int,
    "page": int,
    "size": int
}
```

## 3. Implementation Components

### 3.1 Service Layer Updates
```python
class CargoService:
    def handle_offer_finalization(self, cargo_id: UUID, offer_id: UUID):
        """Handle cargo status change after offer finalization."""
        cargo = self.cargo_repo.find_by_id(cargo_id)
        if cargo.status != "pending":
            raise ValueError("Cargo must be in pending state for offer finalization")
            
        # Begin transaction
        with self.db.transaction():
            # Update cargo status
            self.update_cargo_status(cargo_id, "in_transit")
            
            # Notify route service
            self.route_service.handle_cargo_status_change(
                cargo_id=cargo_id,
                new_status="in_transit"
            )
            
            # Log status change
            self.audit_logger.log_status_change(
                cargo_id=cargo_id,
                old_status="pending",
                new_status="in_transit",
                trigger="offer_finalization",
                offer_id=offer_id
            )

class RouteService:
    def handle_cargo_status_change(self, cargo_id: UUID, new_status: str):
        """Update route status based on cargo status change."""
        route = self.route_repo.find_by_cargo_id(cargo_id)
        
        if new_status == "in_transit":
            self.update_route_status(route.id, "active")
            self._update_timeline_events(route.id)
        elif new_status in ["delivered", "cancelled"]:
            self.update_route_status(route.id, new_status)
```

### 3.2 Required Tests
```python
def test_offer_finalization_success(client, sample_cargo, sample_offer):
    """Test successful offer finalization."""
    response = client.post(
        f"/api/cargo/{sample_cargo.id}/finalize-offer",
        json={"offer_id": str(sample_offer.id)}
    )
    assert response.status_code == 200
    
    # Verify cargo status
    cargo_response = client.get(f"/api/cargo/{sample_cargo.id}")
    assert cargo_response.json["status"] == "in_transit"
    
    # Verify route status
    route_response = client.get(f"/api/route/{sample_cargo.route_id}")
    assert route_response.json["status"] == "active"

def test_offer_finalization_invalid_state(client, sample_cargo):
    """Test offer finalization with invalid cargo state."""
    # Set cargo to in_transit
    sample_cargo.status = "in_transit"
    db.session.commit()
    
    response = client.post(
        f"/api/cargo/{sample_cargo.id}/finalize-offer",
        json={"offer_id": str(uuid.uuid4())}
    )
    assert response.status_code == 400
    assert "must be in pending state" in response.json["error"]
```

## 4. Integration Points

### 4.1 Offer Service Integration
1. Offer finalization triggers cargo status change
2. Validates cargo state before finalization
3. Ensures atomic transaction for status updates
4. Maintains audit trail of status changes

### 4.2 Route Service Integration
1. Synchronizes route status with cargo status
2. Updates timeline events on status change
3. Handles route recalculation if needed
4. Maintains consistency between cargo and route states

## 5. Validation Rules

### 5.1 Create/Update Validation ✅
- Weight must be positive and within limits
- Volume must be positive
- Value must be positive Decimal
- Business entity must exist
- Cargo type must be valid
- Special requirements must be from allowed list

### 5.2 Business Rules 🚧
- Only active business entities can create cargo ✅
- Status transitions must be valid ✅
- Updates restricted in terminal states ✅
- TODO: Business entity certification validation
- TODO: Operating countries validation

## 6. Error Handling ✅

### 6.1 HTTP Status Codes
- 201: Cargo created successfully
- 200: Cargo retrieved/updated successfully
- 400: Invalid request data
- 404: Cargo not found
- 409: Conflict (invalid state transition)
- 500: Server error

### 6.2 Error Response Format
```python
{
    "error": str,
    "details": Optional[Dict],
    "code": str  # Internal error code
}
```

## 7. Success Criteria

### 7.1 Functional Requirements
1. Cargo can only transition to `in_transit` after offer finalization ✅
2. Cargo details cannot be modified in `in_transit` state ✅
3. Route status is synchronized with cargo status ✅
4. All status transitions are properly validated ✅
5. Status changes are properly logged ✅

### 7.2 Technical Requirements
1. All transactions are atomic ✅
2. Status changes are properly audited ✅
3. Integration tests cover the complete flow ✅
4. Error scenarios are properly handled ✅
5. Performance meets requirements ✅

## 8. Dependencies ✅
1. SQLAlchemy models
2. Pydantic schemas
3. Business entity service
4. Validation utilities
5. Error handling middleware

## 9. Future Enhancements (Post-PoC)
1. Advanced cargo validation
2. Cargo templates
3. Bulk operations
4. Historical tracking
5. Status change workflow
6. Document attachments

## 10. Current Implementation Tasks

1. Implement Business Entity Certification Validation
   ```python
   def validate_certifications(self, cargo_type: str, certifications: List[str]) -> bool:
       """Validate if business entity has required certifications for cargo type."""
       required_certs = self.get_required_certifications(cargo_type)
       return all(cert in certifications for cert in required_certs)
   ```

2. Implement Operating Countries Validation
   ```python
   def validate_operating_countries(self, route: Route) -> bool:
       """Validate if business entity can operate in route countries."""
       route_countries = {segment.country_code for segment in route.country_segments}
       return route_countries.issubset(set(self.operating_countries))
   ```

3. Update Tests
   ```python
   def test_certification_validation():
       """Test business entity certification validation."""
       pass  # TODO: Implement test
   
   def test_operating_countries_validation():
       """Test business entity operating countries validation."""
       pass  # TODO: Implement test
   ```

4. Update Documentation
   - Add certification requirements by cargo type
   - Document country operation rules
   - Update API documentation with new validation rules

## 11. Implementation Notes

### Current Implementation
- Basic CRUD operations are fully functional
- Status management system is complete
- Offer integration is working as expected
- Route synchronization is implemented
- Audit logging system is in place

### Remaining Work
1. Business Entity Validation
   - Implement certification checks
   - Add operating countries validation
   - Update relevant documentation
   - Add new test cases

2. Documentation Updates
   - Update API documentation
   - Add new validation rules
   - Document error scenarios
   - Update integration guides
``` 