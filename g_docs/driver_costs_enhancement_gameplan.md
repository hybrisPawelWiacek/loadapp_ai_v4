# Driver Costs and Empty Driving Enhancement Gameplan

## 1. Domain Model Enhancements

### A. Driver Rate Settings
```python
class DriverRateType(str, Enum):
    DAILY_ONLY = "daily_only"           # Fixed daily rate regardless of hours
    DAILY_WITH_HOURS = "daily_with_hours" # Base daily + hourly for driving time
    HOURS_ONLY = "hours_only"           # Hourly rates with overtime

class DriverRates(BaseModel):
    """Enhanced driver rates configuration"""
    rate_type: DriverRateType = DriverRateType.DAILY_WITH_HOURS
    daily_rate: Optional[Decimal]
    regular_hourly_rate: Optional[Decimal]
    overtime_hourly_rate: Optional[Decimal]
    overtime_threshold_hours: Optional[int] = 8

    @validator('daily_rate')
    def validate_daily_rate(cls, v, values):
        if values['rate_type'] in [DriverRateType.DAILY_ONLY, 
                                 DriverRateType.DAILY_WITH_HOURS] and not v:
            raise ValueError("Daily rate required for selected payment type")
        return v

    @validator('regular_hourly_rate')
    def validate_hourly_rate(cls, v, values):
        if values['rate_type'] in [DriverRateType.DAILY_WITH_HOURS,
                                 DriverRateType.HOURS_ONLY] and not v:
            raise ValueError("Hourly rate required for selected payment type")
        return v
```

### B. Enhanced Empty Driving
```python
class EmptyDriving(BaseModel):
    """Empty driving segment before main route."""
    id: UUID
    distance_km: float = Field(default=0.0, ge=0)  # Default 0 for no empty driving
    duration_hours: float = Field(default=0.0, ge=0)
    is_chargeable: bool = Field(default=True)  # New field for optional charging
```

### C. Cost Settings Update
```python
class CostSettings(BaseModel):
    id: UUID
    route_id: UUID
    business_entity_id: UUID
    enabled_components: List[str]
    rates: Dict[str, Decimal]
    driver_rates: Optional[DriverRates] = None  # New field, optional for backward compatibility
```

## 2. Service Layer Changes

### A. Cost Service Updates
```python
class CostService:
    def _calculate_driver_costs(
        self,
        route: Route,
        transport: Transport,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        if "driver" not in settings.enabled_components:
            return self._zero_driver_costs()

        # Use enhanced rates if available, fall back to legacy calculation
        if settings.driver_rates:
            return self._calculate_enhanced_driver_costs(route, settings.driver_rates)
        else:
            return self._calculate_legacy_driver_costs(route, transport, settings)

    def _calculate_enhanced_driver_costs(
        self,
        route: Route,
        driver_rates: DriverRates
    ) -> Dict[str, Decimal]:
        total_hours = Decimal(str(route.total_duration_hours))
        days = (int(total_hours) + 23) // 24

        match driver_rates.rate_type:
            case DriverRateType.DAILY_ONLY:
                return {
                    "base_cost": driver_rates.daily_rate * Decimal(str(days)),
                    "regular_hours_cost": Decimal("0"),
                    "overtime_cost": Decimal("0"),
                    "total_cost": driver_rates.daily_rate * Decimal(str(days))
                }
            
            case DriverRateType.DAILY_WITH_HOURS:
                base_cost = driver_rates.daily_rate * Decimal(str(days))
                regular_hours = min(float(total_hours), 
                                 float(driver_rates.overtime_threshold_hours * days))
                overtime_hours = max(0, float(total_hours) - regular_hours)
                
                regular_cost = Decimal(str(regular_hours)) * driver_rates.regular_hourly_rate
                overtime_cost = (Decimal(str(overtime_hours)) * 
                               (driver_rates.overtime_hourly_rate or 
                                driver_rates.regular_hourly_rate * Decimal("1.5")))
                
                return {
                    "base_cost": base_cost,
                    "regular_hours_cost": regular_cost,
                    "overtime_cost": overtime_cost,
                    "total_cost": base_cost + regular_cost + overtime_cost
                }
            
            case DriverRateType.HOURS_ONLY:
                regular_hours = min(float(total_hours), 
                                 float(driver_rates.overtime_threshold_hours))
                overtime_hours = max(0, float(total_hours) - regular_hours)
                
                regular_cost = Decimal(str(regular_hours)) * driver_rates.regular_hourly_rate
                overtime_cost = (Decimal(str(overtime_hours)) * 
                               driver_rates.overtime_hourly_rate)
                
                return {
                    "base_cost": Decimal("0"),
                    "regular_hours_cost": regular_cost,
                    "overtime_cost": overtime_cost,
                    "total_cost": regular_cost + overtime_cost
                }
```

### B. Route Service Updates
```python
class RouteService:
    def create_route(
        self,
        transport_id: UUID,
        business_entity_id: UUID,
        cargo_id: UUID,
        origin_id: UUID,
        destination_id: UUID,
        pickup_time: datetime,
        delivery_time: datetime,
        truck_location_id: UUID,
        empty_driving_chargeable: bool = True
    ) -> Route:
        # ... existing code ...
        
        # Calculate empty driving if truck location is provided and different from origin
        empty_driving = None
        empty_distance_km = 0.0
        empty_duration_hours = 0.0
        if truck_location_id and truck_location_id != origin_id:
            empty_distance_km, empty_duration_hours = self._route_calculator.calculate_empty_driving(
                truck_location, origin
            )
            empty_driving = EmptyDriving(
                id=uuid4(),
                distance_km=empty_distance_km,
                duration_hours=empty_duration_hours,
                is_chargeable=empty_driving_chargeable
            )
            saved_empty_driving = self._route_repo.save_empty_driving(empty_driving)
```

## 3. API Changes

### A. Cost Settings Endpoint
```python
@router.post("/api/cost/settings/{route_id}")
async def create_cost_settings(
    route_id: UUID,
    settings: CostSettingsCreate,
    business_entity_id: UUID
) -> CostSettings:
    """Create cost settings with enhanced driver rates."""
    return cost_service.create_cost_settings(
        route_id=route_id,
        settings=settings,
        business_entity_id=business_entity_id
    )
```

### B. Route Creation Endpoint
```python
@router.post("/api/routes")
async def create_route(
    transport_id: UUID,
    business_entity_id: UUID,
    cargo_id: UUID,
    origin_id: UUID,
    destination_id: UUID,
    pickup_time: datetime,
    delivery_time: datetime,
    truck_location_id: UUID,
    empty_driving_chargeable: bool = True
) -> Route:
    """Create route with optional empty driving charging."""
    return route_service.create_route(
        transport_id=transport_id,
        business_entity_id=business_entity_id,
        cargo_id=cargo_id,
        origin_id=origin_id,
        destination_id=destination_id,
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        truck_location_id=truck_location_id,
        empty_driving_chargeable=empty_driving_chargeable
    )
```

## 4. Frontend Changes

### A. Driver Rate Settings Form
```python
def render_driver_rate_settings():
    with st.expander("👤 Driver Costs"):
        rate_type = st.selectbox(
            "Payment Type",
            options=[
                "Daily Rate Only",
                "Daily Rate + Hourly",
                "Hourly with Overtime"
            ]
        )
        
        if rate_type in ["Daily Rate Only", "Daily Rate + Hourly"]:
            daily_rate = st.number_input("Daily Rate (EUR)", min_value=0.0)
        
        if rate_type in ["Daily Rate + Hourly", "Hourly with Overtime"]:
            regular_rate = st.number_input("Regular Hourly Rate (EUR)", min_value=0.0)
            overtime_rate = st.number_input("Overtime Hourly Rate (EUR)", min_value=0.0)
            overtime_threshold = st.number_input("Overtime Threshold (hours)", min_value=1)
```

### B. Empty Driving Configuration
```python
def render_empty_driving_config():
    with st.expander("🚛 Empty Driving"):
        is_chargeable = st.checkbox(
            "Charge Empty Driving Costs",
            value=True,
            help="When enabled, empty driving costs will be included in the total"
        )
        
        if st.session_state.get('empty_driving'):
            st.info(f"""
                Empty Driving Details:
                - Distance: {st.session_state.empty_driving.distance_km:.1f} km
                - Duration: {st.session_state.empty_driving.duration_hours:.1f} h
                - Charging: {'Enabled' if is_chargeable else 'Disabled'}
            """)
```

## 5. Implementation Order

1. **Phase 1: Domain Model Updates**
   - Add DriverRateType enum
   - Create DriverRates model
   - Update EmptyDriving model
   - Update CostSettings model

2. **Phase 2: Service Layer**
   - Update CostService with new driver cost calculations
   - Update RouteService with empty driving changes
   - Add validation logic for new models

3. **Phase 3: API Layer**
   - Update cost settings endpoints
   - Update route creation endpoint
   - Add validation for new parameters

4. **Phase 4: Frontend**
   - Add driver rate type selection
   - Add empty driving configuration
   - Update cost preview display

5. **Phase 5: Testing**
   - Unit tests for new rate calculations
   - Integration tests for API changes
   - End-to-end tests for new features

## 6. Migration Plan

1. Add new fields with default values
2. Deploy backend changes
3. Update frontend to support new fields
4. Existing routes continue using legacy calculation
5. New routes can use enhanced features

## 7. Testing Strategy

1. **Unit Tests**
```python
def test_driver_rate_calculations():
    # Test each rate type
    for rate_type in DriverRateType:
        # Test calculation logic
        
def test_empty_driving_charging():
    # Test with and without charging
```

2. **Integration Tests**
- Test complete cost calculation flow
- Verify backward compatibility
- Test edge cases for each rate type

## 8. Documentation Updates

1. Update API documentation
2. Add examples for each rate type
3. Document empty driving options
4. Update user guide with new features 