# Service Layer Refactoring Plan

This document outlines the plan for moving business logic from route handlers to the service layer, ensuring proper separation of concerns and maintainability.

## Overview

The current codebase has business logic scattered in route handlers that should be moved to appropriate service classes. This refactoring will:
- Improve code organization
- Enhance testability
- Ensure consistent validation
- Reduce code duplication
- Make the codebase more maintainable

## Implementation Plan

### 1. Route Service Refactoring (Priority: High)

#### 1.1 Create New Methods in RouteService
```python
- validate_route_creation(transport_id, cargo_id, pickup_time, delivery_time)
- validate_route_feasibility(route_data)
- validate_timeline_events(events)
- update_route_status(route_id, new_status, comment)
```

#### 1.2 Update Route Routes
- Move validation from `/calculate` to service
- Move feasibility check from `/check-feasibility` to service
- Move timeline validation from `/timeline` PUT to service
- Move status management to service

### 2. Cost Service Refactoring (Priority: Medium)

#### 2.1 Add Methods to CostService
```python
- validate_cost_rates(rates)
- validate_cost_settings(settings)
- validate_cost_calculation(route_id)
```

#### 2.2 Update Cost Routes
- Move rate validation from `/settings` endpoints
- Move calculation validation from `/calculate`
- Add proper error handling in service layer

### 3. Offer Service Refactoring (Priority: Medium)

#### 3.1 Enhance OfferService
```python
- validate_margin_percentage(margin)
- manage_offer_status(offer_id, new_status, comment)
- get_offer_status_history(offer_id)
```

#### 3.2 Update Offer Routes
- Move margin validation from `/generate`
- Move status history from `/status`
- Add proper logging in service layer

### 4. Transport Service Creation (Priority: Low)

#### 4.1 Create TransportService
```python
- get_transport_types()
- get_transport_type(type_id)
- get_business_transports(business_id)
```

#### 4.2 Update Transport Routes
- Replace direct DB queries with service calls
- Add proper error handling

## Implementation Order

1. Route Service (highest priority)
   - Most critical business logic
   - Core functionality
   - Other services depend on it

2. Cost Service (medium priority)
   - Depends on route data
   - Critical for offer generation

3. Offer Service (medium priority)
   - Depends on cost calculations
   - Customer-facing functionality

4. Transport Service (low priority)
   - Mostly read operations
   - Less complex business logic

## Implementation Steps for Each Service

1. Write new service methods
   - Add type hints
   - Add docstrings
   - Include validation logic
   - Add error handling

2. Add tests for new methods
   - Unit tests for validation
   - Integration tests for DB operations
   - Edge case coverage

3. Update route handlers
   - Remove business logic
   - Use new service methods
   - Add error handling
   - Update response formats

4. Add logging
   - Service level logging
   - Error tracking
   - Performance monitoring

5. Test complete flow
   - End-to-end testing
   - Error scenarios
   - Edge cases

## Success Criteria

1. All business logic moved to services
2. No direct DB queries in routes
3. Consistent error handling
4. Proper logging throughout
5. Test coverage maintained or improved
6. No regression in functionality

## Risks and Mitigations

1. Risk: Breaking existing functionality
   - Mitigation: Comprehensive testing before/after each change
   - Mitigation: Implement changes incrementally

2. Risk: Performance impact
   - Mitigation: Monitor performance metrics
   - Mitigation: Optimize if needed

3. Risk: Missing edge cases
   - Mitigation: Add extensive test coverage
   - Mitigation: Document assumptions

## Timeline

Estimated timeline for each service:
1. Route Service: 2-3 days
2. Cost Service: 1-2 days
3. Offer Service: 1-2 days
4. Transport Service: 1 day

Total estimated time: 5-8 days

## Future Considerations

1. Consider adding caching layer for frequently accessed data
2. Plan for horizontal scaling of services
3. Consider breaking into microservices if needed
4. Plan for monitoring and observability improvements 