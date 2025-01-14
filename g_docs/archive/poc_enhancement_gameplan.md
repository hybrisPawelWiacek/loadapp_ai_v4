# LoadApp.AI PoC Enhancement Gameplan
Version: 1.3
Last Updated: January 2025

This document outlines the planned enhancements for the LoadApp.AI frontend and its supporting backend changes, building upon the existing Streamlit implementation while maintaining compatibility with the current API structure.

## Part 1: Backend Enhancements

### 1. Cost Settings Enhancements

#### 1.1 Clone Settings Feature
- [X] Implement `clone_cost_settings` method in CostService:
  ```python
  def clone_cost_settings(
      self,
      source_route_id: UUID,
      target_route_id: UUID,
      rate_modifications: Optional[Dict[str, Decimal]] = None
  ) -> CostSettings
  ```
- [X] Add new endpoint `/api/cost/settings/<target_route_id>/clone`
  ```python
  @router.post("/cost/settings/{target_route_id}/clone")
  async def clone_settings(
      target_route_id: UUID,
      source_route_id: UUID,
      rate_modifications: Optional[Dict[str, Dict[str, Decimal]]] = None
  ):
      return await cost_service.clone_cost_settings(
          source_route_id,
          target_route_id,
          rate_modifications
      )
  ```
- [X] Implement validation for source and target routes
- [X] Add support for rate modifications during cloning

#### 1.2 Enhanced Rate Types
- [X] Add RateType enumeration for validation:
  ```python
  class RateType(str, Enum):
      FUEL_RATE = "fuel_rate"
      FUEL_SURCHARGE_RATE = "fuel_surcharge_rate"
      TOLL_RATE = "toll_rate"
      DRIVER_BASE_RATE = "driver_base_rate"
      DRIVER_TIME_RATE = "driver_time_rate"
      EVENT_RATE = "event_rate"
  ```
- [X] Create rate validation schema:
  ```python
  class RateValidationSchema(BaseModel):
      rate_type: RateType
      min_value: Decimal
      max_value: Decimal
      country_specific: bool = False
      requires_certification: bool = False
  ```
- [X] Implement rate validation in CostSettings entity
- [X] Update API documentation with new rate types
- [X] Migration needs:
  ```python
  """Add rate validation schema

  Revision ID: xyz123
  """
  
  def upgrade():
      op.create_table(
          'rate_validation_rules',
          sa.Column('id', sa.UUID(), nullable=False),
          sa.Column('rate_type', sa.String(50), nullable=False),
          sa.Column('min_value', sa.Numeric(10, 2), nullable=False),
          sa.Column('max_value', sa.Numeric(10, 2), nullable=False),
          sa.Column('country_specific', sa.Boolean(), nullable=False),
          sa.Column('requires_certification', sa.Boolean(), nullable=False),
          sa.PrimaryKeyConstraint('id')
      )
  ```

#### 1.3 Driver Cost Enhancement
- [X] Enhance DriverSpecification model:
  ```python
  class DriverSpecification(BaseModel):
      daily_base_rate: Decimal
      driving_time_rate: Decimal  # Per hour
      required_license_type: str
      required_certifications: List[str]
      overtime_rate_multiplier: Optional[Decimal] = Field(default=1.5)
      max_driving_hours: Optional[int] = Field(default=9)
  ```
- [X] Create driver cost calculation service:
  ```python
  class DriverCostCalculationService:
      def calculate_driver_costs(
          self,
          driver_spec: DriverSpecification,
          route_timeline: RouteTimeline
      ) -> DriverCostBreakdown:
          regular_hours = min(
              route_timeline.total_driving_hours,
              driver_spec.max_driving_hours
          )
          overtime_hours = max(
              0,
              route_timeline.total_driving_hours - driver_spec.max_driving_hours
          )
          
          return DriverCostBreakdown(
              base_cost=driver_spec.daily_base_rate * route_timeline.total_days,
              regular_hours_cost=driver_spec.driving_time_rate * regular_hours,
              overtime_cost=(
                  driver_spec.driving_time_rate *
                  driver_spec.overtime_rate_multiplier *
                  overtime_hours
              )
          )
  ```
- [X] Update driver cost calculation to include time-based rates
- [X] Modify cost breakdown response to show detailed driver costs
- [X] Migration needs:
  ```python
  """Add driver cost specifications

  Revision ID: abc456
  """
  
  def upgrade():
      op.add_column('driver_specifications',
          sa.Column('driving_time_rate', sa.Numeric(10, 2), nullable=False),
          sa.Column('overtime_rate_multiplier', sa.Numeric(3, 2),
                   server_default='1.5'),
          sa.Column('max_driving_hours', sa.Integer, server_default='9')
      )
  ```

#### 1.4 Toll Calculator Enhancement
- [X] Extend TollCalculationPort interface:
  ```python
  def calculate_toll(
      self,
      segment: CountrySegment,
      truck_specs: dict,
      overrides: Optional[dict] = None
  ) -> Decimal
  ```
- [X] Create toll rate override schema:
  ```python
  class TollRateOverride(BaseModel):
      vehicle_class: str
      rate_multiplier: Decimal
      country_code: str
      route_type: Optional[str] = None
  ```
- [X] Update TollRateAdapter implementation
- [X] Add support for vehicle class overrides
- [X] Migration needs:
  ```python
  """Add toll rate overrides

  Revision ID: def789
  """
  
  def upgrade():
      op.create_table(
          'toll_rate_overrides',
          sa.Column('id', sa.UUID(), nullable=False),
          sa.Column('vehicle_class', sa.String(50), nullable=False),
          sa.Column('rate_multiplier', sa.Numeric(3, 2), nullable=False),
          sa.Column('country_code', sa.String(2), nullable=False),
          sa.Column('route_type', sa.String(50)),
          sa.PrimaryKeyConstraint('id')
      )
  ```

#### 1.5 Partial Updates Support
- [X] Add PATCH endpoint for cost settings updates:
  ```python
  @router.patch("/cost/settings/{route_id}")
  async def update_cost_settings(
      route_id: UUID,
      updates: Dict[str, Any]
  ):
      return await cost_service.update_cost_settings(route_id, updates)
  ```
- [X] Implement partial update logic in CostService:
  ```python
  def update_cost_settings(
      self,
      route_id: UUID,
      updates: Dict[str, Any]
  ) -> CostSettings:
      settings = self.get_cost_settings(route_id)
      for key, value in updates.items():
          if hasattr(settings, key):
              setattr(settings, key, value)
      return self.save_cost_settings(settings)
  ```
- [X] Add validation for partial updates

### 2. Business Entity Support
- [X] Create business entity model:
  ```python
  class BusinessEntity(BaseModel):
      id: UUID
      name: str
      certifications: List[str]
      operating_countries: List[str]
      default_cost_settings: Optional[Dict[str, Any]]
      active: bool = True
  ```
- [X] Create new `/api/business-entity` endpoint:
  ```python
  @router.get("/business-entity")
  async def list_business_entities() -> List[BusinessEntity]:
      return await business_service.list_active_entities()
  ```
- [X] Add business entity validation in cost calculations
- [X] Migration needs:
  ```python
  """Add business entities

  Revision ID: ghi012
  """
  
  def upgrade():
      op.create_table(
          'business_entities',
          sa.Column('id', sa.UUID(), nullable=False),
          sa.Column('name', sa.String(100), nullable=False),
          sa.Column('certifications', sa.ARRAY(sa.String), nullable=False),
          sa.Column('operating_countries', sa.ARRAY(sa.String), nullable=False),
          sa.Column('default_cost_settings', sa.JSON),
          sa.Column('active', sa.Boolean(), nullable=False),
          sa.PrimaryKeyConstraint('id')
      )
  ```
- [X] Add seed data for business entities:
  - EcoTrans GmbH (Berlin)
    * Eco-friendly transport company
    * ISO 9001, ISO 14001, GDP, SQAS certifications
    * Operating in DE, PL, CZ, AT, NL
    * Higher rates due to eco-friendly practices
  - SpeedLog Express (Warsaw)
    * Fast logistics provider
    * ISO 9001, AEO, TAPA FSR certifications
    * Operating in PL, DE, CZ, SK, HU, LT
    * Competitive rates with security focus
  - HeavyHaul Solutions (Utrecht)
    * Specialized heavy transport
    * ISO 9001, DEKRA, IMCA, LEEA certifications
    * Operating in NL, DE, BE, FR
    * Premium rates for specialized services

### 3. Testing & Documentation
- [X] Add unit tests for new service methods:
  - Business service tests (validation, certification checks)
  - Cost service tests (rate validation, settings management)
  - Entity validation tests (business entity fields)
- [X] Add integration tests for new endpoints:
  - Business routes API tests
  - Repository integration tests
  - Model persistence tests
- [X] Update API documentation with new endpoints and features:
  - Business entity endpoints
  - Cost settings endpoints
  - Rate validation endpoints
  - Error responses and examples
- [X] Document rate type validation rules:
  - FUEL_RATE (0.50 - 5.00 EUR/L)
  - TOLL_RATE (0.10 - 2.00 EUR/km)
  - DRIVER_BASE_RATE (100.00 - 500.00 EUR/day)
  - DRIVER_TIME_RATE (10.00 - 100.00 EUR/hour)
  - EVENT_RATE (20.00 - 200.00 EUR/event)

## Part 2: Frontend Enhancements

### 1. Core UI Improvements

#### 1.1 Navigation & Layout
- [x] Implement multi-tab interface with clear workflow progression
  - Route & Cargo Input
  - Route Visualization
  - Cost Management
  - Offer Generation
- [x] Add persistent session state management using `st.session_state`
- [x] Create a status bar showing current phase in the workflow

#### 1.2 Input Phase Enhancements
- [x] Add business entity selection dropdown at the start
- [x] Enhance location input with address autocomplete
- [x] Improve transport type selection with detailed specifications display
- [x] Add input validation with real-time feedback
- [x] Create collapsible sections for better form organization

#### 1.3 Route Visualization Improvements
- [x] Enhance map visualization
  - Color-coded route segments by country
  - Interactive markers for timeline events
  - Empty driving segment visualization (200km/4h)
  - Hover tooltips with segment details
- [x] Create an enhanced timeline visualization
  - Visual timeline with event markers
  - Duration bars between events
  - Status indicators (completed, pending, etc.)
  - Interactive event details

### 2. Enhanced Cost Management Interface

#### 2.1 Cost Settings Interface
- [x] Create expandable cost component sections
  - Route-related costs (fuel, toll, driver)
  - Cargo-related costs (handling, special requirements)
  - Business activity costs (overhead, administrative)
  - Timeline event costs
- [x] Add component-specific configuration panels
  - Fuel rate configuration per country
  - Toll rate adjustments by vehicle class
  - Driver cost settings (base rate and time-based rate)
  - Event-specific cost settings
- [x] Add "Clone Settings" functionality
  - Source route selection
  - Rate modification interface
  - Preview changes

#### 2.2 Cost Visualization
- [x] Implement interactive cost breakdown
  - Pie chart for cost distribution
  - Bar charts for country-specific costs
  - Cost comparison views
- [x] Add cost summary cards with key metrics
- [x] Create detailed cost reports with expandable sections
- [x] Add driver cost breakdown visualization
  - Base rate costs
  - Time-based costs
  - Total driver costs

### 3. Offer Generation Improvements

#### 3.1 Offer Configuration
- [x] Add AI enhancement toggle with preview
- [x] Create margin configuration with profit visualization
- [x] Implement offer template selection (if supported by API)

#### 3.2 Offer Visualization
- [x] Enhance offer display
  - Professional layout for offer details
  - Cost breakdown section
  - AI-enhanced content section
  - Fun facts section with toggle
- [x] Add offer actions
  - Save offer
  - Export to PDF (if supported)
  - Share offer (if supported)

### 4. General Enhancements

#### 4.1 User Experience
- [x] Add loading indicators for all async operations
- [x] Implement error handling with user-friendly messages
- [x] Create help tooltips for complex features
- [x] Add input validation with immediate feedback

#### 4.2 Data Management
- [x] Implement session persistence
- [x] Add route/offer history view
- [x] Create data export functionality

### 5. Testing & Documentation

#### 5.1 Testing
- [ ] Create test cases for all new UI components
- [ ] Implement integration tests with backend
- [ ] Add error scenario testing

#### 5.2 Documentation
- [ ] Update user documentation
- [ ] Create technical documentation for new features
- [ ] Document API integration points

## Implementation Notes

1. All frontend enhancements have been implemented using Streamlit's capabilities
2. Backend changes were completed before frontend implementation
3. Each feature was implemented incrementally, ensuring backward compatibility
4. Testing will be performed at each step to maintain stability

## Progress Tracking

- [x] Core UI improvements completed
- [x] Input phase enhancements implemented
- [x] Route visualization improvements added
- [x] Cost management interface enhanced
- [x] Offer generation improvements completed
- [x] General enhancements implemented
- [ ] Testing & documentation pending

## Next Steps

1. Implement comprehensive test suite
2. Create user and technical documentation
3. Document API integration points
4. Perform final testing and validation 