# Toll Calculation Mode Enhancement Gameplan

## Overview
Add user control over how toll costs are calculated, allowing choice between manual rates from settings and dynamic real-time calculation.

## 1. Data Model Changes

### A. Add Toll Calculation Mode Enum
```python
class TollCalculationMode(str, Enum):
    MANUAL = "manual"  # Use rates from cost settings
    DYNAMIC = "dynamic"  # Calculate in real-time using TollCalculationPort
```

### B. Enhance Cost Settings Entity
```python
class CostSettings:
    toll_calculation_mode: TollCalculationMode = TollCalculationMode.MANUAL  # Default to manual
```

### C. Enhanced Toll Cost Result Structure
```python
class TollCostResult:
    amount: Decimal
    calculation_mode: TollCalculationMode
    rate_used: Decimal
    calculation_details: Dict[str, Any]  # For storing method-specific details
```

## 2. Backend Changes

### A. Repository Layer
1. Update CostSettingsRepository
   - Modify schema to include toll_calculation_mode
   - Update CRUD operations to handle new field

### B. Domain Layer
1. Update CostService._calculate_toll_costs
   ```python
   def _calculate_toll_costs(self, route, transport, settings, business):
       if settings.toll_calculation_mode == TollCalculationMode.MANUAL:
           # Use rates from settings
           return self._calculate_manual_toll_costs(...)
       else:
           # Use dynamic calculation
           return self._calculate_dynamic_toll_costs(...)
   ```

2. Add helper methods for different calculation modes
   - _calculate_manual_toll_costs
   - _calculate_dynamic_toll_costs
   - Methods to format and store calculation details

### C. API Layer
1. Modify cost settings endpoints
   - Update request/response schemas
   - Add validation for toll_calculation_mode

2. Enhance toll rates endpoint
   - Add dynamic rates calculation
   - Include calculation details in response

3. Update cost calculation endpoint
   - Include calculation mode and details in response

## 3. Frontend Changes

### A. Cost Settings View
1. Add Toll Calculation Mode Toggle
   ```python
   with st.expander("🛣️ Toll Rates"):
       mode = st.toggle(
           "Use Dynamic Toll Calculation",
           help="Toggle between manual rates and dynamic calculation"
       )
   ```

2. Add Explanatory UI Elements
   - Information about each mode
   - Impact on cost calculation
   - Visual indicators for active mode

### B. Cost Preview Section
1. Enhance Toll Costs Display
   ```python
   st.markdown("#### 🛣️ Toll Costs by Country")
   for country, cost_details in toll_costs.items():
       st.write(f"Country: {country}")
       st.write(f"Rate Used: {cost_details.rate_used}")
       st.write(f"Calculation Mode: {cost_details.calculation_mode}")
       if cost_details.calculation_mode == "dynamic":
           st.write("Calculation Details:", cost_details.calculation_details)
   ```

## 4. API Changes

### A. Cost Settings Endpoints
1. POST/PUT `/api/cost/settings/<route_id>`
   ```json
   Request:
   {
       "enabled_components": ["fuel", "toll", ...],
       "toll_calculation_mode": "manual"|"dynamic",
       "rates": { ... }
   }
   ```

### B. Toll Rates Endpoint
1. GET `/api/cost/rates/toll/<route_id>`
   ```json
   Response:
   {
       "default_rates": { ... },
       "current_settings": { ... },
       "dynamic_rates": {
           "DE": {
               "calculated_rate": "0.24",
               "calculation_details": {
                   "base_rate": "0.20",
                   "adjustments": { ... }
               }
           }
       },
       "vehicle_info": { ... }
   }
   ```

### C. Cost Calculation Endpoint
1. POST `/api/cost/calculate/<route_id>`
   ```json
   Response:
   {
       "breakdown": {
           "toll_costs": {
               "DE": {
                   "amount": "25.82",
                   "calculation_mode": "manual"|"dynamic",
                   "rate_used": "0.24",
                   "calculation_details": { ... }
               }
           }
       }
   }
   ```

## 5. Implementation Order

1. **Phase 1: Data Model & Backend Core**
   - Implement TollCalculationMode enum
   - Update CostSettings entity
   - Modify repositories
   - Update CostService calculation logic

2. **Phase 2: API Layer**
   - Update endpoints
   - Add new response structures
   - Implement validation

3. **Phase 3: Frontend**
   - Add toggle UI
   - Update cost settings view
   - Enhance cost preview display

4. **Phase 4: Testing & Refinement**
   - Add unit tests for new functionality
   - Test both calculation modes
   - Verify UI feedback
   - Performance testing for dynamic calculation

## 6. Testing Strategy

1. **Unit Tests**
   - Test both calculation modes
   - Verify rate selection logic
   - Test API response formats

2. **Integration Tests**
   - Test mode switching
   - Verify calculation results
   - Test UI updates

3. **Manual Testing**
   - Verify UI feedback
   - Check calculation details display
   - Test edge cases

## 7. Migration Plan

1. Default all existing routes to manual mode
2. Add database migration for new field
3. Update existing cost settings entries
4. Verify existing calculations still work

## 8. Documentation Updates

1. Update API documentation
2. Add user guide for new feature
3. Update technical documentation
4. Add examples for both modes 