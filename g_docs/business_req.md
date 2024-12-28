# Transport Manager Flow & Requirements

## 1. Route & Cargo Input Phase

The Transport Manager starts by entering basic route and cargo information:

### Required Inputs
- Origin ('From' location)
- Destination ('To' location)
- Transport type selection:
  * Flatbed
  * Livestock
  * Container
  * Plandeka
  * Oversized
- Pickup date and time
- Delivery date and time
- Cargo details:
  * Weight
  * Value
  * Special requirements

## 2. Route Calculation Phase

Triggered when Transport Manager clicks "Calculate Route":

### A. Compliance Checks
- Verify truck/driver can handle transport type
- Check business entity paperwork
- Note: For PoC, always returns true

### B. Route Generation
1. Main Calculations:
   - Use Google Maps to determine distances and duration
   - Add empty driving (fixed 200km/4h before main route)

2. Timeline Creation:
   - Add pickup event (1 hour duration)
   - Add one rest event in middle (1 hour duration)
   - Add delivery event (1 hour duration)

3. Additional Processing:
   - Generate country segments for toll calculations

### C. Frontend Display
Must show:
- Map with route segments and events
- Timeline visualization
- Total distance and duration
- Compliance check results
- Route feasibility status (always true in PoC)

### D. Available Actions
- "Show other feasible routes" (disabled in PoC)
- "Optimize route" (disabled in PoC)
- "Save route" (active)

## 3. Cost Management Phase

### A. Cost Settings Management

When the Transport Manager clicks "Configure Cost Settings":

1. **Cost Settings Form Display**
   - System retrieves current cost settings from database
   - Displays comprehensive settings form
   - Shows all available cost components by category

2. **Settings Configuration Options**
   - Enable/disable specific cost components
   - Configure component-specific settings
   - Review current values and make adjustments

3. **Settings Persistence**
   - "Save Cost Settings" button saves configuration
   - Settings stored in database for specific route
   - Settings become basis for cost calculations

### B. Cost Structure & Components

#### 1. Route-Related Costs
These costs are directly tied to the specific route:

1. **Fuel Costs**
   - Calculation based on:
     * Empty driving consumption (0.22 L/km baseline)
     * Loaded consumption (0.29 L/km baseline)
     * Additional 0.3L/km per ton of cargo (including fuel in tank)
   - Country-specific fuel prices
   - Separate tracking for empty vs loaded segments

2. **Toll Charges**
   - Country-specific rates
   - Factors affecting cost:
     * Number of axles
     * EURO class
     * CO2 class
     * Distance per country
   - Example: DE: 0.187 EUR/km for EURO VI

3. **Parking Costs**
   - Per-stop basis
   - Country-specific rates
   - Different rates for:
     * Germany vs Austria parking
     * Secured vs unsecured facilities
   - Example: 30 EUR for secured parking in Austria

4. **Driver Costs** (Key Component)
   - Base Daily Salary: 138 EUR/day
   - Duration-based multiplication
   - Additional components:
     * Driver accommodation costs
     * Compliance with country minimum wages
     * Meal allowances
     * Per-event costs (e.g., dinner)
     * Time-based costs (e.g., hours in specific country)

#### 2. Cargo-Related Costs
Specific to cargo type and requirements:

1. **Pre-Transport Requirements**
   - Cleaning before loading
   - Vacuum testing if required
   - Disinfection procedures
   - Example: 150 EUR for pre-cleaning

2. **Handling Requirements**
   - Export customs clearance
   - Veterinary costs for specific cargo
   - Customs transit costs
   - Temperature control requirements
   - Example: 11.1 EUR for courier service

3. **Post-Transport Requirements**
   - Cleaning after delivery
   - Residue utilization
   - Documentation fees
   - Example: 150 EUR for post-cleaning

#### 3. Business Activity Costs
Fixed and overhead costs per route:

1. **Vehicle-Related**
   - Leasing costs (85 EUR/day for tautliner)
   - Depreciation (45 EUR/day)
   - General cleaning
   - Technical costs (GPS, IT support)

2. **Administrative**
   - Insurance OC/AC
   - Permits and licenses
   - Stationary costs
   - Certificates (ISO, SQAS, HACCP)

#### 4. Extra Route-Specific Costs
Additional costs that may apply:

1. **Support Services**
   - Translator/loading assistance (10 EUR/service)
   - Representative costs
   - Additional equipment needs
   - Documentation services

### B. Cost Calculation Process
When "Calculate Costs" is clicked:

1. Base Calculations:
   - Multiply daily rates by route duration
   - Calculate country-specific costs
   - Apply cargo-specific requirements

2. Component Processing:
   - Sum all enabled cost categories
   - Apply country-specific rules
   - Calculate timeline event costs

3. Final Steps:
   - Generate cost breakdown
   - Show costs by category
   - Save complete calculation
   - Display cost breakdown

Note: For PoC, cost components can be toggled on/off, but base rates are fixed.

## 4. Offer Generation Phase

### A. Basic Offer Creation
When "Generate Offer" is clicked:
1. Take calculated costs
2. Apply specified margin
3. Generate basic offer

### B. AI Enhancement
When "Generate AI Offer" is selected:
1. Send to AI service
2. Display enhanced content
3. Show transport-related fun fact
4. Save complete offer with AI content

## Implementation Notes

### PoC Simplifications
1. Empty Driving:
   - Fixed 200km distance
   - Fixed 4-hour duration
   - Always added before main route

2. Route Feasibility:
   - All routes marked as feasible
   - Basic validation only

3. Disabled Features:
   - Alternative routes
   - Route optimization
   - Cost settings revision after initial setup

### Required Validations
1. Basic Input:
   - All locations must be valid
   - Dates/times must be logical
   - Cargo details must be complete

2. Business Rules:
   - Weight within limits
   - Value must be positive
   - Timeline must be feasible

### Screen Requirements
1. Main Screen:
   - Route input form
   - Map display
   - Timeline visualization
   - Cost controls
   - Offer generation

2. Settings Screen:
   - Cost component toggles
   - Basic rate inputs
   - Component management

3. Review Screen:
   - Previous routes
   - Saved offers
   - Cost histories
