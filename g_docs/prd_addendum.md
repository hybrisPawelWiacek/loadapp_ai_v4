# LoadApp.AI PRD Addendum
Version: 1.0  
Date: January 2025

This addendum addresses minor concerns and "quick-win" improvements to the LoadApp.AI PoC, grouped by main functional areas of the transport flow. It supplements the original PoC Product Requirements Document (prd.md) and is intended to guide upcoming feature expansions and refinements.

---

## 1. Cargo

### 1.1 Minor Enhancements or Gaps
• Add Cargo Dimension Fields (length, width, height) to better validate specialized cargo (oversized, hazardous, etc.).  
• Introduce Hazardous Material Codes for specialized cargo checks (ADR, special licensing).  
• Enhance Cargo Deletion Logic to handle cargo in other intermediate statuses (e.g., “ready_for_pickup”) or split cargo scenarios.  

### 1.2 Quick-Win Improvements
1. (Business-level) Provide a dedicated screen to edit cargo “special requirements” after creation.  
2. (Technical) Extend the existing cargo form or add a multi-step input wizard in the frontend to capture advanced cargo details.  
3. (Technical) Add optional "cargo_dimensions" or "cargo_hazard_code" fields in backend code. If left blank, the system remains backward-compatible.

---

## 2. Route Creation

### 2.1 Minor Enhancements or Gaps
• Advanced feasibility checks: Presently, routes are always marked as feasible in the PoC (simple boolean flag). Further logic around road restrictions or advanced distance/time constraints could be helpful.  
• Additional rest events: Currently, only one “rest” event is created. Real-world scenarios might require multiple rest stops based on driver regulations.

### 2.2 Quick-Win Improvements
1. (Business-level) Permit the user to insert an optional “second rest event” if total route duration exceeds a threshold, e.g. 8 hours.  
2. (Technical) Add a route-calculation configuration parameter (like “required_rest_interval”) set to a default for maximum flexibility.  
3. (Business-level) Introduce an optional “Route Alternative” feature stub, so the system can display a second route with partial data. This is a simple extension that can illustrate route selection.

---

## 3. Cost Settings

### 3.1 Minor Enhancements or Gaps
• After initial creation, reconfiguring cost settings is lightly supported. More robust update endpoints or UI flows would allow iterative toggling of cost components.  
• Detailed domain-level checks (e.g., mandatory overhead for certain cargo types, dynamic rates by region) remain placeholders in the PoC.

### 3.2 Quick-Win Improvements
1. (Technical) Add a “PUT /api/cost/settings/<route_id>” or similar endpoint for partial updates of cost settings, so users can adjust components without fully recreating them.  
2. (Business-level) Provide a minimal caching / duplication feature (“Clone Settings From Another Route”). This helps a manager quickly reuse cost settings from a comparable route.

---

## 4. Costs (Calculation & Breakdown)

### 4.1 Minor Enhancements or Gaps
• Fuel/toll rates are mostly static or rely on simplified logic. Real-time data or per-country complexities can be integrated if needed.  
• Current cost toggles are purely on/off. Adjusting partial rates (like “driver cost for overnight only”) or more nuanced overhead calculations could be beneficial.

### 4.2 Quick-Win Improvements
1. (Technical) Expose an optional “fuel_surcharge_rate” in cost settings for easy global adjustments.  
2. (Business-level) Provide a cost summary snapshot that can be exported to PDF or CSV for quick review.  
3. (Technical) Leverage a more dynamic approach to toll calculations by letting the front-end pass “Euro class” or “vehicle weight” overrides that differ from the stored defaults.

---

## 5. Offer

### 5.1 Minor Enhancements or Gaps
• The “AI Offer” feature is in place, but additional content or style parameters could be user-configurable (tone, length, bullet points).  
• Implementation of advanced “Offer Revisions” or “Counter-offer” workflows remain out of the PoC scope.

### 5.2 Quick-Win Improvements
1. (Business-level) Store multiple drafted or revised offers for the same route (versioning).  
2. (Technical) Expose optional parameters (e.g., “offer_tone,” “format_type”) that get passed to the OpenAI service.  
3. (Business-level) Provide end-user disclaimers or disclaimers logic in the final AI output, clarifying it’s an AI-generated text snippet.

---

## 6. Technical Considerations

1. All enhancements above should be backward-compatible with the existing database schema or introduced as optional fields.  
2. Logging approach can be standardized across endpoints (Cargo, Cost, Offer, etc.). At the PoC level, each blueprint does minimal logging differently. Consistent, structured logs facilitate easier debugging.  
3. Integration Points:
   • Toll rate expansions: Optionally integrate dynamic third-party APIs using the existing “TollRateService.”  
   • Route generation alternatives: Expand the “GoogleMapsService” usage to support multiple route calculations.  
   • Offer content customization: Provide extended parameters through “OpenAIService” for style or brand voice.  

---

## 7. Summary and Next Steps

The items above provide relatively straightforward opportunities to strengthen the PoC or transition to a more production-ready environment. They require minimal changes to the main code flow or database structure. Adopting them gradually, grouped by functional area, will enhance the overall experience and allow a solid demonstration of advanced transport management functionalities.

1. Align each improvement with the existing architectural approach (clean architecture, domain-driven design).  
2. Prioritize each improvement by business value and development effort.  
3. Target the “quick-win” items first, ensuring the PoC remains stable and easily demonstrable.  

## 8. Additional Technical Implementation Notes
To successfully integrate the enhancements listed above with minimal disruption to the existing PoC, consider these practices:

1. Database Schema & Entities  
   • Leverage optional columns or JSON fields for new attributes. For instance, “cargo_dimensions” in CargoModel can store length/width/height as a JSON string if you wish to remain compatible with the current schema.  
   • Keep PoC defaults (e.g., single rest event, always “true” feasibility) and only extend where the user specifically requests more detail.  

2. Service Layer Expansion  
   • Update existing domain services (cost_service.py, offer_service.py, route_service.py) with optional parameters instead of mandatory changes, ensuring backward compatibility.  
   • For route calculations (route_service.py), add a “rest_interval_threshold” to dynamically insert an extra timeline event if pickup-to-delivery durations exceed a certain threshold.  

3. Reusable Repositories & Adapters  
   • For “Clone Settings From Another Route,” create a small helper method in cost_service.py that duplicates a CostSettings object from an existing route_id to a new route_id.  
   • In toll_rate_service.py, consider introducing an optional “vehicle_weight_override” parameter. If present, it modifies the base rate logic to accommodate a user-supplied weight instead of the truck_specs defaults.  

4. Logging & Workflow Consistency  
   • Consolidate logging patterns. For instance, unify the “INFO” and “DEBUG” calls by adopting the same data structure and keys (e.g., extra={...}) across all blueprint endpoints.  
   • Revisit error handling patterns. Some endpoints rollback transactions on errors, some do not. Standardize this approach for easier debugging.  

5. Frontend Adjustments  
   • If implementing extra cargo data (e.g., cargo dimensions), add optional fields to the Streamlit form with conditionally displayed inputs. Any omitted fields remain defaulted on the backend.  
   • Provide toggles or dropdowns for advanced features (like “Insert Second Rest Stop”), passing that user preference to the route calculation endpoint as “rest_interval_threshold.”  

6. Testing Strategy  
   • For each new domain entity or optional parameter, write or extend tests in existing modules (e.g., tests/backend/domain/entities) rather than placing them in new files. This keeps the PoC structure simple.  
   • If adding advanced features like “Route Alternative,” consider separate test functions that verify fallback to PoC defaults if no alternative route is requested.  

7. Phased Rollout  
   • Implement a feature flag approach or environment variable toggles (like ENABLE_ADVANCED_CARGO). This ensures you can demonstrate PoC-level functionality to some business stakeholders without confusion from new features.  
   • Expand beyond the PoC in small increments, verifying each addition via existing test suites and optional new integration tests.


## 9. Minor Style Variations & Proposed Solutions
There are some differences across our endpoints concerning transaction handling and logging:

1. Transaction Rollback Consistency  
   In certain routes, we explicitly call rollback() upon exceptions, while others rely on either implicit teardown logic or partial error capture. Though both approaches can work, making rollback usage consistent in every endpoint will simplify debugging and ensure the DB session is always clean after failures.  
   • (Technical) Adopt a uniform rollback pattern. For instance, always wrap database calls in try/except, and on exception, call db.rollback() or raise a well-defined error.  
   • (Business-level) Inform the user if a rollback occurs, e.g., “An error has occurred; no changes were saved.”

2. Logging Levels & Uniform Patterns  
   Some endpoints (Cargo, Route) have more extensive structured logging than others (Cost, Transport). The latter often rely on minimal logs or common debug messages.  
   • (Technical) Add consistent DEBUG-level logs across services (including infrastructure adapters like toll_rate_service.py or openai_service.py) to capture routine operations (e.g., successful calculations, intermediate states).  
   • (Technical) Reserve INFO-level logs for major lifecycle events (creation, successful completion, external service calls).  
   • (Business-level) Ensure that any errors or partial successes are also logged at a sufficiently high level (WARN or ERROR).  


   **End of Addendum**  