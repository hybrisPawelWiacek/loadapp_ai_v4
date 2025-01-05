import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import Dict, Any, List, Optional
from .shared_utils import api_request, format_currency

# Constants for cost components
COST_COMPONENTS = {
    'fuel': 'Fuel Costs',
    'toll': 'Toll Charges',
    'driver': 'Driver Costs',
    'overhead': 'Business Overhead',
    'events': 'Event Costs (loading/unloading)'
}

def create_cost_settings(route_id: str, data: Dict) -> Optional[Dict]:
    """Create cost settings for a route."""
    return api_request(
        f"/api/cost/settings/{route_id}",
        method="POST",
        data=data
    )

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
    """Validate if a rate value is within allowed ranges."""
    ranges = {
        'fuel_rate': (0.50, 5.00),
        'fuel_surcharge_rate': (0.01, 0.50),
        'toll_rate': (0.10, 2.00),
        'driver_base_rate': (100.00, 500.00),
        'driver_time_rate': (10.00, 100.00),
        'event_rate': (20.00, 200.00)
    }
    
    if rate_type not in ranges:
        return False
    
    min_val, max_val = ranges[rate_type]
    return min_val <= value <= max_val

def create_cost_charts(breakdown: Optional[Dict] = None) -> List[go.Figure]:
    """Create visualizations for cost breakdown."""
    if not breakdown:
        return []
        
    charts = []
    try:
        # Create pie chart for cost distribution
        fuel_costs = breakdown.get('fuel_costs', {})
        toll_costs = breakdown.get('toll_costs', {})
        driver_costs = breakdown.get('driver_costs', 0)
        overhead_costs = breakdown.get('overhead_costs', 0)
        
        if not isinstance(fuel_costs, dict):
            fuel_costs = {}
        if not isinstance(toll_costs, dict):
            toll_costs = {}
            
        total_fuel = sum(float(v) for v in fuel_costs.values())
        total_toll = sum(float(v) for v in toll_costs.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=['Fuel', 'Toll', 'Driver', 'Overhead'],
            values=[total_fuel, total_toll, float(driver_costs), float(overhead_costs)],
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