import streamlit as st
import pandas as pd
from utils.shared_utils import api_request, format_currency
from utils.cost_utils import (
    COST_COMPONENTS,
    create_cost_charts,
    display_cost_metrics,
    display_event_costs,
    validate_rate
)
from typing import Union
import traceback

def display_cost_settings(route_id: str) -> dict:
    """Display and configure cost settings."""
    st.markdown("### Cost Settings")
    
    # Clone settings option
    with st.expander("📋 Clone Settings from Another Route"):
        st.info("Feature coming soon: Clone cost settings from previous routes")
        
    # Component enablement
    st.markdown("#### Enable Cost Components")
    enabled_components = []
    for comp_id, comp_name in COST_COMPONENTS.items():
        if st.checkbox(comp_name, value=True, key=f"cost_comp_{comp_id}"):
            enabled_components.append(comp_id)
    
    # Rate configuration
    st.markdown("#### Configure Rates")
    rates = {}
    
    # Fuel rates by country
    with st.expander("⛽ Fuel Rates"):
        st.markdown("Set fuel rates per country:")
        route = st.session_state.get('route_data', {})
        for segment in route.get('country_segments', []):
            if not isinstance(segment, dict):
                continue
            country = segment.get('country_code')
            if not country:
                continue
            rate = st.number_input(
                f"Fuel Rate for {country} (EUR/L)",
                min_value=0.5,
                max_value=5.0,
                value=1.5,
                step=0.1,
                help=f"Set fuel rate for {country} (0.50-5.00 EUR/L)"
            )
            if validate_rate('fuel_rate', rate):
                rates[f'fuel_rate_{country}'] = rate
            else:
                st.error(f"Invalid fuel rate for {country}")
    
    # Driver costs
    with st.expander("👤 Driver Costs"):
        st.markdown("Configure driver-related costs:")
        base_rate = st.number_input(
            "Daily Base Rate (EUR/day)",
            min_value=100.0,
            max_value=500.0,
            value=200.0,
            step=10.0,
            help="Set daily base rate (100-500 EUR/day)"
        )
        if validate_rate('driver_base_rate', base_rate):
            rates['driver_base_rate'] = base_rate
        
        time_rate = st.number_input(
            "Time-based Rate (EUR/hour)",
            min_value=10.0,
            max_value=100.0,
            value=25.0,
            step=5.0,
            help="Set hourly rate (10-100 EUR/hour)"
        )
        if validate_rate('driver_time_rate', time_rate):
            rates['driver_time_rate'] = time_rate
        
    # Toll rates
    with st.expander("🛣️ Toll Rates"):
        st.markdown("Configure toll rates per country:")
        for segment in route.get('country_segments', []):
            if not isinstance(segment, dict):
                continue
            country = segment.get('country_code')
            if not country:
                continue
            rate = st.number_input(
                f"Toll Rate for {country} (EUR/km)",
                min_value=0.1,
                max_value=2.0,
                value=0.2,
                step=0.1,
                help=f"Set toll rate for {country} (0.10-2.00 EUR/km)"
            )
            if validate_rate('toll_rate', rate):
                rates[f'toll_rate_{country}'] = rate
            else:
                st.error(f"Invalid toll rate for {country}")
    
    # Event costs
    with st.expander("📅 Event Costs"):
        st.markdown("Set costs for timeline events:")
        event_rate = st.number_input(
            "Standard Event Rate (EUR/event)",
            min_value=20.0,
            max_value=200.0,
            value=50.0,
            step=10.0,
            help="Set standard rate per event (20-200 EUR/event)"
        )
        if validate_rate('event_rate', event_rate):
            rates['event_rate'] = event_rate
        else:
            st.error("Invalid event rate")
    
    # Save settings button
    if st.button("Save Cost Settings", type="primary"):
        with st.spinner("Saving cost settings..."):
            settings_data = {
                "enabled_components": enabled_components,
                "rates": rates
            }
            settings = api_request(
                f"/api/cost/settings/{route_id}",
                method="POST",
                data=settings_data
            )
            if settings:
                st.success("Cost settings saved successfully!")
                # Calculate costs automatically after saving settings
                costs = api_request(
                    f"/api/cost/calculate/{route_id}",
                    method="POST"
                )
                if costs:
                    st.session_state.current_costs = costs
                    st.session_state.cost_data = costs
                    st.rerun()
                return settings
    
    return None

def display_cost_breakdown(breakdown: dict):
    """Display enhanced cost breakdown details."""
    if not breakdown:
        st.warning("No cost breakdown available")
        return
        
    # Display cost metrics
    display_cost_metrics(breakdown)
    
    # Detailed breakdowns in expandable sections
    with st.expander("🔍 Detailed Cost Breakdown"):
        # Fuel costs by country
        st.markdown("#### ⛽ Fuel Costs by Country")
        fuel_costs = breakdown.get('fuel_costs', {})
        if fuel_costs:
            fuel_data = []
            total_fuel = sum(float(v) for v in fuel_costs.values())
            for country, cost in fuel_costs.items():
                fuel_data.append({
                    'Country': country,
                    'Cost': format_currency(float(cost)),
                    'Percentage': f"{(float(cost)/total_fuel)*100:.1f}%" if total_fuel > 0 else "0%"
                })
            st.dataframe(
                pd.DataFrame(fuel_data),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No fuel costs available")
        
        # Toll costs by country
        st.markdown("#### 🛣️ Toll Costs by Country")
        toll_costs = breakdown.get('toll_costs', {})
        if toll_costs:
            toll_data = []
            total_toll = sum(float(v) for v in toll_costs.values())
            for country, cost in toll_costs.items():
                toll_data.append({
                    'Country': country,
                    'Cost': format_currency(float(cost)),
                    'Percentage': f"{(float(cost)/total_toll)*100:.1f}%" if total_toll > 0 else "0%"
                })
            st.dataframe(
                pd.DataFrame(toll_data),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No toll costs available")
        
        # Driver costs
        st.markdown("#### 👤 Driver Costs")
        if 'driver_costs' in breakdown:
            display_driver_costs(breakdown['driver_costs'])
        else:
            st.info("No driver costs available")
        
        # Event costs
        st.markdown("#### 📅 Event Costs")
        if 'timeline_event_costs' in breakdown:
            display_event_costs(breakdown['timeline_event_costs'])
        else:
            st.info("No event costs available")
        
        # Overhead costs
        if 'overhead_costs' in breakdown and 'total_cost' in breakdown:
            overhead = float(breakdown['overhead_costs'])
            total = float(breakdown['total_cost'])
            st.metric(
                "💼 Overhead Costs",
                format_currency(overhead),
                delta=f"{(overhead/total)*100:.1f}%" if total > 0 else "0%"
            )
        else:
            st.info("No overhead costs available")

def display_cost_management():
    """Display the cost management interface."""
    st.subheader("Cost Management")
    
    route = st.session_state.get('route_data')
    if not route:
        st.error("No route data available")
        return
    
    # Create two columns for settings and preview
    settings_col, preview_col = st.columns([1, 1])
    
    with settings_col:
        settings = display_cost_settings(route.get('id'))
    
    with preview_col:
        st.markdown("### Cost Preview")
        
        costs = st.session_state.get('current_costs')
        if costs and isinstance(costs, dict):
            breakdown = costs.get('breakdown')
            if breakdown:
                # Create visualizations
                charts = create_cost_charts(breakdown)
                if charts:
                    for chart in charts:
                        st.plotly_chart(chart)
                
                # Display detailed breakdown
                display_cost_breakdown(breakdown)
                
                # Add proceed button
                if st.button("Proceed to Offer Generation", type="primary"):
                    st.session_state.should_navigate_to_offer = True
                    st.rerun()
            else:
                st.info("No cost breakdown available")
        else:
            st.info("Save cost settings to see the cost breakdown") 

def parse_driver_costs(driver_costs):
    """Helper function to parse driver costs from various formats."""
    try:
        if isinstance(driver_costs, dict):
            parsed_costs = driver_costs
        elif isinstance(driver_costs, str):
            import json
            # Remove any whitespace and handle double-encoded JSON
            driver_costs = driver_costs.strip()
            
            # First try direct JSON parsing
            try:
                parsed_costs = json.loads(driver_costs)
            except json.JSONDecodeError:
                # If that fails, try handling double-encoded JSON
                try:
                    # Replace escaped quotes and handle nested JSON
                    cleaned = driver_costs.replace('\\"', '"').replace("'", '"')
                    if cleaned.startswith('"') and cleaned.endswith('"'):
                        # Remove outer quotes for double-encoded JSON
                        cleaned = cleaned[1:-1]
                    parsed_costs = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    # If still fails, try one more time with minimal cleaning
                    minimal_clean = driver_costs.replace("'", '"')
                    parsed_costs = json.loads(minimal_clean)
        else:
            raise ValueError(f"Expected string or dictionary, got {type(driver_costs)}")

        # Ensure we have a dictionary at this point
        if not isinstance(parsed_costs, dict):
            raise ValueError(f"Parsing result is not a dictionary: {type(parsed_costs)}")

        # Convert all values to float, handling string Decimal representations
        return {
            'base_cost': float(str(parsed_costs.get('base_cost', '0')).replace(',', '')),
            'regular_hours_cost': float(str(parsed_costs.get('regular_hours_cost', '0')).replace(',', '')),
            'overtime_cost': float(str(parsed_costs.get('overtime_cost', '0')).replace(',', '')),
            'total_cost': float(str(parsed_costs.get('total_cost', '0')).replace(',', ''))
        }
        
    except Exception as e:
        # Add more context to the error message
        raise ValueError(f"Failed to parse driver costs (type: {type(driver_costs)}): {str(e)}")

def display_driver_costs(driver_costs: Union[dict, str]):
    """Display driver costs breakdown."""
    try:
        # Parse the costs into a consistent format
        costs = parse_driver_costs(driver_costs)
        
        # Display the breakdown using columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Base Cost", format_currency(costs['base_cost']))
            st.metric("Regular Hours", format_currency(costs['regular_hours_cost']))
        
        with col2:
            st.metric("Overtime", format_currency(costs['overtime_cost']))
            st.metric("Total Driver Cost", format_currency(costs['total_cost']))
        
        # Add visualization
        total = costs['total_cost']
        if total > 0:
            st.write("Cost Distribution:")
            base_pct = (costs['base_cost'] / total) * 100
            reg_pct = (costs['regular_hours_cost'] / total) * 100
            ot_pct = (costs['overtime_cost'] / total) * 100
            
            st.progress(base_pct/100, f"Base ({base_pct:.1f}%)")
            st.progress(reg_pct/100, f"Regular Hours ({reg_pct:.1f}%)")
            if ot_pct > 0:
                st.progress(ot_pct/100, f"Overtime ({ot_pct:.1f}%)")
            
    except Exception as e:
        st.error(f"Error displaying driver costs: {str(e)}")

def display_cost_preview(cost_breakdown: dict):
    """Display cost preview section with charts."""
    try:
        # Get the total cost first (needed for percentages)
        total_cost = float(cost_breakdown.get('total_cost', 0))
        
        # Display costs overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fuel_costs = sum(float(cost) for cost in cost_breakdown.get('fuel_costs', {}).values())
            st.metric("Fuel Costs", f"€{fuel_costs:.2f}", delta=f"{(fuel_costs/total_cost)*100:.1f}%")
            
        with col2:
            toll_costs = sum(float(cost) for cost in cost_breakdown.get('toll_costs', {}).values())
            st.metric("Toll Charges", f"€{toll_costs:.2f}", delta=f"{(toll_costs/total_cost)*100:.1f}%")
            
        with col3:
            st.metric("Total Cost", f"€{total_cost:.2f}")

        # Detailed breakdown section
        with st.expander("📊 Detailed Cost Breakdown", expanded=True):
            # Driver costs breakdown
            st.subheader("👨‍✈️ Driver Costs")
            driver_costs = cost_breakdown.get('driver_costs', {})
            if driver_costs:
                display_driver_costs(driver_costs)
            else:
                st.info("No driver costs available")

            # Add a divider
            st.divider()

    except Exception as e:
        st.error(f"Error creating cost preview: {str(e)}") 