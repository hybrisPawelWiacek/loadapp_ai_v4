import streamlit as st
import pandas as pd
from utils.shared_utils import api_request, format_currency
from utils.cost_utils import (
    COST_COMPONENTS,
    create_cost_charts,
    display_cost_metrics,
    display_driver_costs,
    display_event_costs,
    validate_rate
)

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
        
        rates['overtime_multiplier'] = st.slider(
            "Overtime Rate Multiplier",
            min_value=1.0,
            max_value=2.0,
            value=1.5,
            step=0.1,
            help="Multiplier for overtime hours"
        )
    
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
                    st.session_state.workflow_step = 4
                    st.rerun()
            else:
                st.info("No cost breakdown available")
        else:
            st.info("Save cost settings to see the cost breakdown") 