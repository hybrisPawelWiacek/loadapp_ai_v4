import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import Dict, Any, List, Optional
from .shared_utils import api_request, format_currency
import traceback

# Constants for cost components
COST_COMPONENTS = {
    'fuel': 'Fuel Costs',
    'toll': 'Toll Charges',
    'driver': 'Driver Costs',
    'overhead': 'Business Overhead',
    'events': 'Event Costs (loading/unloading)'
}

# Rate validation ranges
RATE_RANGES = {
    'fuel_rate': (0.5, 5.0),
    'toll_rate': (0.1, 2.0),
    'driver_base_rate': (100.0, 500.0),
    'driver_time_rate': (10.0, 100.0),
    'event_rate': (10.0, 200.0),
    'overhead_rate': (0.01, 1000.0),
    'overhead_admin_rate': (0.01, 1000.0),
    'overhead_insurance_rate': (0.01, 1000.0),
    'overhead_facilities_rate': (0.01, 1000.0),
    'overhead_other_rate': (0.0, 1000.0)
}

def create_cost_settings(route_id: str, data: Dict) -> Optional[Dict]:
    """Create cost settings for a route."""
    print(f"[DEBUG] Creating cost settings for route_id: {route_id}")
    print(f"[DEBUG] Cost settings data: {data}")
    try:
        # Convert all numeric values to strings to ensure consistent handling
        rates = data.get('rates', {})
        converted_rates = {}
        for key, value in rates.items():
            try:
                converted_rates[key] = str(float(value))
                print(f"[DEBUG] Converted rate {key}: {value} -> {converted_rates[key]}")
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] Error converting rate {key}: {str(e)}")
                raise ValueError(f"Invalid rate value for {key}: {value}")
        
        data['rates'] = converted_rates
        print(f"[DEBUG] Converted cost settings data: {data}")
        
        try:
            response = api_request(
                f"/api/cost/settings/{route_id}",
                method="POST",
                data=data,
                _debug=True  # Enable debug mode for the API request
            )
            print(f"[DEBUG] Raw API response: {response}")
            
            if response is None:
                print("[DEBUG] API request returned None")
                return None
                
            if isinstance(response, dict):
                if 'error' in response:
                    print(f"[DEBUG] API returned error: {response['error']}")
                    raise ValueError(response['error'])
                print(f"[DEBUG] API response: {response}")
                return response
            else:
                print(f"[DEBUG] Unexpected response type: {type(response)}")
                return None
                
        except Exception as e:
            print(f"[DEBUG] API request failed: {str(e)}")
            print(f"[DEBUG] API request traceback: {traceback.format_exc()}")
            raise
            
    except Exception as e:
        print(f"[DEBUG] Error in create_cost_settings: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        raise

def update_cost_settings(route_id: str, data: Dict) -> Optional[Dict]:
    """Update cost settings for a route."""
    return api_request(
        f"/api/cost/settings/{route_id}",
        method="PUT",
        data=data
    )

def patch_cost_settings(route_id: str, data: Dict) -> Optional[Dict]:
    """Partially update cost settings."""
    return api_request(
        f"/api/cost/settings/{route_id}",
        method="PATCH",
        data=data
    )

def clone_cost_settings(target_route_id: str, source_route_id: str, modifications: Dict = None) -> Optional[Dict]:
    """Clone cost settings from one route to another."""
    data = {
        "source_route_id": source_route_id
    }
    if modifications:
        data["rate_modifications"] = modifications
    
    return api_request(
        f"/api/cost/settings/{target_route_id}/clone",
        method="POST",
        data=data
    )

def get_cost_settings(route_id: str) -> Optional[Dict]:
    """Get cost settings for a route."""
    return api_request(f"/api/cost/settings/{route_id}")

def calculate_costs(route_id: str) -> Optional[Dict]:
    """Calculate costs for a route."""
    return api_request(f"/api/cost/calculate/{route_id}", method="POST")

def get_cost_breakdown(route_id: str) -> Optional[Dict]:
    """Get cost breakdown for a route."""
    return api_request(f"/api/cost/breakdown/{route_id}")

def validate_rate(rate_type: str, value: float) -> bool:
    """Validate a rate value against its allowed range."""
    try:
        print(f"[DEBUG] Validating rate: {rate_type} = {value}")
        if rate_type not in RATE_RANGES:
            print(f"[DEBUG] Unknown rate type: {rate_type}")
            return False
            
        min_val, max_val = RATE_RANGES[rate_type]
        print(f"[DEBUG] Rate range for {rate_type}: {min_val} - {max_val}")
        
        try:
            value = float(value)
            print(f"[DEBUG] Converted value to float: {value}")
        except (ValueError, TypeError) as e:
            print(f"[DEBUG] Failed to convert value to float: {str(e)}")
            return False
            
        is_valid = min_val <= value <= max_val
        print(f"[DEBUG] Rate validation result for {rate_type}: {is_valid} (value={value}, range={min_val}-{max_val})")
        
        if not is_valid:
            print(f"[DEBUG] Rate validation failed for {rate_type}: value={value}, range=({min_val}, {max_val})")
        return is_valid
    except Exception as e:
        print(f"[DEBUG] Rate validation error for {rate_type}: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return False

def create_cost_charts(breakdown: Optional[Dict] = None) -> List[go.Figure]:
    """Create visualizations for cost breakdown."""
    if not breakdown:
        return []
        
    charts = []
    try:
        # Create pie chart for cost distribution
        fuel_costs = breakdown.get('fuel_costs', {})
        toll_costs = breakdown.get('toll_costs', {})
        driver_costs = breakdown.get('driver_costs', {})
        overhead_costs = breakdown.get('overhead_costs', 0)
        
        if not isinstance(fuel_costs, dict):
            fuel_costs = {}
        if not isinstance(toll_costs, dict):
            toll_costs = {}
        if not isinstance(driver_costs, dict):
            driver_costs = {}
            
        total_fuel = sum(float(v) for v in fuel_costs.values())
        total_toll = sum(float(v) for v in toll_costs.values())
        total_driver = float(driver_costs.get('total_cost', 0))
        total_overhead = float(overhead_costs)
        
        fig = go.Figure(data=[go.Pie(
            labels=['Fuel', 'Toll', 'Driver', 'Overhead'],
            values=[total_fuel, total_toll, total_driver, total_overhead],
            hole=.3
        )])
        fig.update_layout(title='Cost Distribution')
        charts.append(fig)
        
        return charts
    except Exception as e:
        st.error(f"Error creating cost charts: {str(e)}")
        return []

def display_cost_metrics(breakdown: Optional[Dict] = None):
    """Display key cost metrics."""
    st.subheader("Cost Overview")
    
    if not breakdown:
        st.error("No cost data available")
        st.metric("Total Cost", format_currency(0))
        return
        
    try:
        total_cost = float(breakdown.get('total_cost', 0))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fuel_costs = breakdown.get('fuel_costs', {})
            if not isinstance(fuel_costs, dict):
                fuel_costs = {}
            fuel_cost = sum(float(v) for v in fuel_costs.values())
            st.metric(
                "Fuel Costs",
                format_currency(fuel_cost),
                delta=f"{(fuel_cost/total_cost)*100:.1f}%" if total_cost > 0 else "0%"
            )
        
        with col2:
            toll_costs = breakdown.get('toll_costs', {})
            if not isinstance(toll_costs, dict):
                toll_costs = {}
            toll_cost = sum(float(v) for v in toll_costs.values())
            st.metric(
                "Toll Charges",
                format_currency(toll_cost),
                delta=f"{(toll_cost/total_cost)*100:.1f}%" if total_cost > 0 else "0%"
            )
        
        with col3:
            st.metric(
                "Total Cost",
                format_currency(total_cost)
            )
    except Exception as e:
        st.error(f"Error displaying cost metrics: {str(e)}")
        st.metric("Total Cost", format_currency(0))

def display_driver_costs(breakdown: Optional[Dict] = None):
    """Display driver-related costs."""
    st.subheader("Driver Costs")
    
    if not breakdown:
        st.info("No driver cost data available")
        return
        
    try:
        driver_cost = float(breakdown.get('driver_costs', 0))
        total_cost = float(breakdown.get('total_cost', 0))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Driver Cost",
                format_currency(driver_cost),
                delta=f"{(driver_cost/total_cost)*100:.1f}% of total" if total_cost > 0 else "0%"
            )
        
        with col2:
            if 'driver_details' in breakdown:
                details = breakdown['driver_details']
                if isinstance(details, dict):
                    st.metric(
                        "Working Hours",
                        f"{details.get('working_hours', 0)}h",
                        delta=f"{details.get('overtime_hours', 0)}h overtime"
                    )
    except Exception as e:
        st.error(f"Error displaying driver costs: {str(e)}")

def display_event_costs(breakdown: Optional[Dict] = None):
    """Display timeline event costs."""
    st.subheader("Event Costs")
    
    if not breakdown:
        st.info("No event cost data available")
        st.metric("Total Event Cost", format_currency(0))
        return
        
    try:
        event_costs = breakdown.get('timeline_event_costs', {})
        if not isinstance(event_costs, dict):
            event_costs = {}
            
        if event_costs:
            total_event_cost = 0
            for event_type, cost in event_costs.items():
                try:
                    cost_value = float(cost)
                    total_event_cost += cost_value
                    st.metric(
                        f"{event_type.title()} Cost",
                        format_currency(cost_value)
                    )
                except (ValueError, TypeError):
                    continue
            st.metric("Total Event Cost", format_currency(total_event_cost))
        else:
            st.info("No event costs recorded")
            st.metric("Total Event Cost", format_currency(0))
    except Exception as e:
        st.error(f"Error displaying event costs: {str(e)}")
        st.metric("Total Event Cost", format_currency(0)) 