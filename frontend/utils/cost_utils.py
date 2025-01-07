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

# Consumption rates (L/km)
CONSUMPTION_RATES = {
    "empty": 0.22,    # Empty driving
    "loaded": 0.29,   # Loaded driving
    "per_ton": 0.03   # Additional per ton of cargo
}

# Rate validation ranges
RATE_RANGES = {
    'fuel_rate': (0.5, 5.0),
    'toll_rate': (0.1, 2.0),
    'driver_base_rate': (100.0, 500.0),
    'driver_time_rate': (10.0, 100.0),
    'driver_overtime_rate': (15.0, 150.0),
    'pickup_rate': (20.0, 200.0),
    'delivery_rate': (20.0, 200.0),
    'rest_rate': (20.0, 150.0),
    'overhead_admin_rate': (0.01, 1000.0),
    'overhead_insurance_rate': (0.01, 1000.0),
    'overhead_facilities_rate': (0.01, 1000.0),
    'overhead_other_rate': (0.0, 1000.0)
}

def fetch_route_fuel_rates(route_id: str) -> Optional[Dict]:
    """Fetch fuel rates specific to a route's countries.
    
    Args:
        route_id: ID of the route to fetch rates for
        
    Returns:
        Dict containing:
        - default_rates: Dict[country_code, rate]
        - current_settings: Dict[rate_key, value]
        - consumption_rates: Dict[type, rate]
    """
    try:
        print(f"[DEBUG] Fetching fuel rates for route_id: {route_id}")
        response = api_request(f"/api/cost/rates/fuel/{route_id}", method="GET", _debug=True)
        print(f"[DEBUG] Fuel rates response: {response}")
        return response
    except Exception as e:
        print(f"[DEBUG] Error fetching fuel rates: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return None

def fetch_event_rates() -> Optional[Dict]:
    """Fetch event rates and ranges.
    
    Returns:
        Dict containing:
        - rates: Dict[event_type, rate]
        - ranges: Dict[event_type, (min_rate, max_rate)]
    """
    try:
        return api_request("/api/cost/rates/event", method="GET")
    except Exception as e:
        print(f"[DEBUG] Error fetching event rates: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return None

def validate_rate(rate_type: str, value: float) -> bool:
    """Validate a rate value against its allowed range.
    
    Args:
        rate_type: Type of rate to validate (e.g. 'fuel_rate', 'toll_rate_DE')
        value: Rate value to validate
        
    Returns:
        bool: True if rate is valid, False otherwise
    """
    try:
        print(f"[DEBUG] Validating rate: {rate_type} = {value}")
        
        # Handle country-specific rates (e.g. 'toll_rate_DE')
        base_rate_type = rate_type
        if '_' in rate_type:
            parts = rate_type.split('_')
            if len(parts) > 2 and len(parts[-1]) == 2:  # Country code format check
                base_rate_type = '_'.join(parts[:-1])
        
        # Handle event-specific rates
        if base_rate_type.endswith('_rate'):
            event_type = base_rate_type.replace('_rate', '')
            if event_type in ['pickup', 'delivery', 'rest']:
                base_rate_type = f'{event_type}_rate'
        
        if base_rate_type not in RATE_RANGES:
            print(f"[DEBUG] Unknown rate type: {base_rate_type}")
            return False
            
        min_val, max_val = RATE_RANGES[base_rate_type]
        is_valid = min_val <= value <= max_val
        
        if not is_valid:
            print(f"[DEBUG] Rate validation failed: {value} not in range [{min_val}, {max_val}]")
        
        return is_valid
        
    except Exception as e:
        print(f"[DEBUG] Rate validation error: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return False

def create_cost_settings(route_id: str, settings_data: dict) -> Optional[dict]:
    """Create cost settings for a route."""
    try:
        print(f"[DEBUG] Creating cost settings for route_id: {route_id}")
        print(f"[DEBUG] Cost settings data: {settings_data}")
        
        # Convert numeric values to strings for API
        if 'rates' in settings_data:
            converted_data = {
                'enabled_components': settings_data['enabled_components'],
                'rates': {}
            }
            for rate_key, rate_value in settings_data['rates'].items():
                # Keep rate keys in lowercase except for country codes
                if '_rate_' in rate_key:
                    # Split the key to handle country-specific rates
                    parts = rate_key.split('_')
                    if len(parts) > 2 and len(parts[-1]) == 2:  # Country code format check
                        # Convert country code to uppercase
                        parts[-1] = parts[-1].upper()
                        rate_key = '_'.join(parts)
                print(f"[DEBUG] Converting rate {rate_key}: {rate_value} -> {str(rate_value)}")
                converted_data['rates'][rate_key] = str(rate_value)
            settings_data = converted_data
            
        print(f"[DEBUG] Converted cost settings data: {settings_data}")
        
        # Make API request
        response = api_request(
            f"/api/cost/settings/{route_id}",
            method="POST",
            data=settings_data,
            _debug=True
        )
        
        if isinstance(response, dict) and 'error' in response:
            print(f"[DEBUG] API returned error: {response}")
            raise ValueError(response['error'])
            
        if not response:
            print("[DEBUG] API request failed")
            raise ValueError("API request failed")
            
        return response
        
    except Exception as e:
        print(f"[DEBUG] Error in create_cost_settings: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        raise ValueError(str(e))

def update_cost_settings(route_id: str, data: Dict) -> Optional[Dict]:
    """Update cost settings for a route."""
    try:
        # First get existing settings to preserve country-specific rates
        existing_settings = get_cost_settings(route_id)
        if not existing_settings:
            print("[DEBUG] No existing settings found")
            raise ValueError("No existing settings found")
            
        # Get existing rates
        existing_rates = existing_settings.get('rates', {})
        print(f"[DEBUG] Existing rates: {existing_rates}")
        
        # Convert numeric values to strings for API and merge with existing rates
        if 'rates' in data:
            converted_data = {
                'enabled_components': data['enabled_components'],
                'rates': dict(existing_rates)  # Start with existing rates
            }
            for rate_key, rate_value in data['rates'].items():
                # Handle country-specific rates
                if '_rate_' in rate_key:
                    # Split the key to handle country-specific rates
                    parts = rate_key.split('_')
                    if len(parts) > 2 and len(parts[-1]) == 2:  # Country code format check
                        # Convert country code to uppercase
                        parts[-1] = parts[-1].upper()
                        rate_key = '_'.join(parts)
                print(f"[DEBUG] Converting rate {rate_key}: {rate_value} -> {str(rate_value)}")
                converted_data['rates'][rate_key] = str(rate_value)
            data = converted_data
            
        print(f"[DEBUG] Converted cost settings data: {data}")
        
        response = api_request(
            f"/api/cost/settings/{route_id}",
            method="PUT",
            data=data
        )
        
        if isinstance(response, dict) and 'error' in response:
            print(f"[DEBUG] API returned error: {response}")
            raise ValueError(response['error'])
            
        if not response:
            print("[DEBUG] API request failed")
            raise ValueError("API request failed")
            
        return response
        
    except Exception as e:
        print(f"[DEBUG] Error in update_cost_settings: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        raise ValueError(str(e))

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
    try:
        response = api_request(f"/api/cost/settings/{route_id}", method="GET")
        if isinstance(response, dict) and 'error' in response:
            print(f"[DEBUG] API returned error: {response}")
            return None
        return response
    except Exception as e:
        print(f"[DEBUG] Error in get_cost_settings: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return None

def calculate_costs(route_id: str) -> Optional[Dict]:
    """Calculate costs for a route."""
    return api_request(f"/api/cost/calculate/{route_id}", method="POST")

def get_cost_breakdown(route_id: str) -> Optional[Dict]:
    """Get cost breakdown for a route."""
    return api_request(f"/api/cost/breakdown/{route_id}")

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