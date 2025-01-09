import streamlit as st
import pandas as pd
from decimal import Decimal
from utils.shared_utils import api_request, format_currency
from utils.cost_utils import (
    COST_COMPONENTS,
    create_cost_charts,
    display_cost_metrics,
    display_event_costs,
    validate_rate,
    create_cost_settings,
    calculate_costs,
    fetch_route_fuel_rates,
    fetch_route_toll_rates,
    fetch_event_rates,
    CONSUMPTION_RATES,
    get_cost_settings,
    update_cost_settings
)
from typing import Union
import traceback

def display_cost_settings(route_id: str) -> dict:
    """Display and configure cost settings."""
    st.markdown("### Cost Settings")
    
    # Initialize settings
    settings = {
        'enabled_components': [],
        'rates': {}
    }
    
    # Fetch existing settings if available
    existing_settings = get_cost_settings(route_id)
    if existing_settings:
        settings = existing_settings
    
    # Add toll calculation mode toggle
    with st.expander("🛣️ Toll Settings"):
        # Get the current toll mode from session state or default to Manual
        toll_mode = st.radio(
            "Toll Calculation Mode",
            options=["Manual", "Dynamic"],
            index=0,  # Default to Manual
            help="Choose between manual toll rates or dynamic calculation",
            key="toll_calculation_mode"
        )
        
        # Store the mode in session state for other components to access
        st.session_state.toll_mode = toll_mode
        
        # Show different content based on mode
        if toll_mode == "Manual":
            st.markdown("#### Manual Toll Rates")
            
            # Fetch toll rates for the route
            toll_rates = fetch_route_toll_rates(route_id)
            if toll_rates:
                default_rates = toll_rates.get('default_rates', {})
                current_settings = toll_rates.get('current_settings', {})
                
                # Display toll rates for each country
                for country, rates in default_rates.items():
                    st.markdown(f"##### {country} Toll Settings")
                    
                    # Get current rate for this country
                    rate_key = f"toll_rate_{country}"
                    current_rate = current_settings.get(rate_key, rates.get('toll_class_rates', {}).get('1', '0.0'))
                    
                    # Input for toll rate
                    new_rate = st.number_input(
                        f"Toll Rate (EUR/km)",
                        min_value=0.0,
                        max_value=5.0,
                        value=float(current_rate),
                        step=0.01,
                        key=f"toll_rate_{country}",
                        help=f"Set toll rate for {country}"
                    )
                    
                    # Store the rate in settings
                    settings['rates'][rate_key] = str(new_rate)
                    
                    # Show vehicle class information
                    with st.expander(f"{country} Vehicle Class Details"):
                        st.write("Base rates by toll class:")
                        for toll_class, rate in rates.get('toll_class_rates', {}).items():
                            st.write(f"• Class {toll_class}: €{rate}/km")
                        
                        st.write("\nEuro class adjustments:")
                        for euro_class, adjustment in rates.get('euro_class_adjustments', {}).items():
                            st.write(f"• EURO {euro_class}: €{adjustment}/km")
            else:
                st.warning("Could not fetch toll rates. Using default values.")
                
        else:  # Dynamic mode
            st.info("""
                🚧 Dynamic toll calculation is coming soon! 
                This feature will automatically calculate toll costs based on:
                - Vehicle class
                - Route segments
                - Real-time rates
                
                For now, manual rates will be used for calculations.
            """)
            
            # Show current manual rates in read-only format
            toll_rates = fetch_route_toll_rates(route_id)
            if toll_rates and toll_rates.get('current_settings'):
                st.markdown("#### Current Manual Rates (Read-only)")
                for rate_key, rate_value in toll_rates['current_settings'].items():
                    if rate_key.startswith('toll_rate_'):
                        country = rate_key.split('_')[-1]
                        st.text(f"{country}: €{rate_value}/km")
    
    # Add toll component to enabled components if any toll rates are set
    if any(key.startswith('toll_rate_') for key in settings['rates']):
        if 'toll' not in settings['enabled_components']:
            settings['enabled_components'].append('toll')
    
    # Continue with other cost settings sections
    with st.expander("⛽ Fuel Settings"):
        fuel_rates = fetch_route_fuel_rates(route_id)
        if fuel_rates:
            st.markdown("#### Fuel Rates")
            default_rates = fuel_rates.get('default_rates', {})
            current_settings = fuel_rates.get('current_settings', {})
            
            for country, rate in default_rates.items():
                rate_key = f"fuel_rate_{country}"
                current_rate = current_settings.get(rate_key, rate)
                
                new_rate = st.number_input(
                    f"Fuel Rate for {country} (EUR/L)",
                    min_value=0.5,
                    max_value=5.0,
                    value=float(current_rate),
                    step=0.01,
                    key=f"fuel_rate_{country}"
                )
                settings['rates'][rate_key] = str(new_rate)
            
            # Show consumption rates
            st.markdown("#### Consumption Rates")
            for rate_type, rate in CONSUMPTION_RATES.items():
                st.text(f"{rate_type.replace('_', ' ').title()}: {rate} L/km")
    
    with st.expander("👨‍✈️ Driver Settings"):
        event_rates = fetch_event_rates()
        if event_rates:
            st.markdown("#### Driver Rates")
            rates = event_rates.get('rates', {})
            ranges = event_rates.get('ranges', {})
            
            for event_type, rate in rates.items():
                rate_range = ranges.get(event_type, [20.0, 200.0])
                new_rate = st.number_input(
                    f"{event_type.title()} Rate (EUR)",
                    min_value=float(rate_range[0]),
                    max_value=float(rate_range[1]),
                    value=float(rate),
                    step=1.0,
                    key=f"{event_type}_rate"
                )
                settings['rates'][f"{event_type}_rate"] = str(new_rate)
    
    # Save button
    if st.button("Save Cost Settings"):
        try:
            if existing_settings:
                updated_settings = update_cost_settings(route_id, settings)
            else:
                updated_settings = create_cost_settings(route_id, settings)
            
            if updated_settings:
                st.success("Cost settings saved successfully!")
                st.session_state.should_refresh_costs = True
            else:
                st.error("Failed to save cost settings")
        except Exception as e:
            st.error(f"Error saving cost settings: {str(e)}")
    
    return settings

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
        
        # Check if we need to refresh costs
        if st.session_state.get('should_refresh_costs'):
            costs = calculate_costs(route.get('id'))
            if costs:
                st.session_state['current_costs'] = costs
            st.session_state['should_refresh_costs'] = False
        
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