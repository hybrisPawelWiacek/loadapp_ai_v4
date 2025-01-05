import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.route_utils import (
    get_route_timeline, update_route_timeline,
    get_route_segments, get_route_status_history,
    update_route_status, display_timeline_events,
    display_route_segments, display_route_status_history,
    validate_timeline_event, check_route_feasibility,
    get_empty_driving, update_empty_driving,
    optimize_route
)
from utils.map_utils import create_route_map
from utils.shared_utils import format_currency
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

def render_route_view():
    """Enhanced route planning view."""
    st.title("Route Planning")
    
    route_data = st.session_state.get('route_data')
    if not route_data:
        st.info("No route data available")
        return
    
    route_id = route_data.get('id')
    if not route_id:
        st.error("Invalid route data")
        return
    
    # Create tabs for different route aspects
    tabs = st.tabs([
        "Overview",
        "Timeline Management",
        "Route Segments",
        "Empty Driving",
        "Optimization",
        "Status History"
    ])
    
    with tabs[0]:
        render_route_overview(route_data)
    
    with tabs[1]:
        render_timeline_management(route_id)
    
    with tabs[2]:
        render_route_segments(route_id)
    
    with tabs[3]:
        render_empty_driving_management(route_id)
    
    with tabs[4]:
        render_route_optimization(route_id)
    
    with tabs[5]:
        render_status_management(route_id)

def render_route_overview(route_data: Dict):
    """Enhanced route overview with feasibility check."""
    st.subheader("Route Overview")
    
    # Basic metrics
    col1, col2, col3 = st.columns(3)
    
    # Display metrics directly on column objects
    col1.metric(
        "Total Distance",
        f"{route_data.get('total_distance_km', 0)} km",
        help="Total distance including empty driving"
    )
    
    col2.metric(
        "Total Duration",
        f"{route_data.get('total_duration_hours', 0)} hours",
        help="Total duration including stops"
    )
    
    col3.metric(
        "Status",
        route_data.get('status', 'NEW'),
        help="Current route status"
    )
    
    # Feasibility check
    with st.expander("Route Feasibility", expanded=True):
        feasibility = check_route_feasibility(route_data['id'])
        if feasibility:
            if feasibility.get('is_feasible'):
                st.success("✅ Route is feasible")
            else:
                st.warning("⚠️ Route may not be feasible")
            
            # Display validation details
            st.subheader("Validation Details")
            for check, result in feasibility.get('validation_details', {}).items():
                if result:
                    st.success(f"✓ {check}")
                else:
                    st.error(f"✗ {check}")
    
    # Display route map
    st.subheader("Route Map")
    map_data = {
        'timeline_events': route_data.get('timeline_events', []),
        'country_segments': route_data.get('country_segments', []),
        'empty_driving': route_data.get('empty_driving')
    }
    route_map = create_route_map(map_data)
    folium_static(route_map, width=800, height=400)

def render_empty_driving_management(route_id: str):
    """Empty driving management interface."""
    st.subheader("Empty Driving Management")
    
    empty_driving = get_empty_driving(route_id)
    if not empty_driving:
        st.info("No empty driving configuration available")
        return
    
    with st.form("empty_driving_form"):
        st.write("Configure Empty Driving")
        
        col1, col2 = st.columns(2)
        with col1:
            start_address = st.text_input(
                "Start Location",
                value=empty_driving.get('start_location', {}).get('address', ''),
                help="Where the empty driving segment begins"
            )
        
        with col2:
            end_address = st.text_input(
                "End Location",
                value=empty_driving.get('end_location', {}).get('address', ''),
                help="Where the empty driving segment ends"
            )
        
        # Additional configuration options
        include_fuel = st.checkbox(
            "Include Fuel Costs",
            value=empty_driving.get('include_fuel_costs', True),
            help="Calculate fuel costs for empty driving"
        )
        
        include_toll = st.checkbox(
            "Include Toll Costs",
            value=empty_driving.get('include_toll_costs', True),
            help="Calculate toll costs for empty driving"
        )
        
        if st.form_submit_button("Update Empty Driving"):
            update_data = {
                "start_address": start_address,
                "end_address": end_address,
                "include_fuel_costs": include_fuel,
                "include_toll_costs": include_toll
            }
            
            result = update_empty_driving(route_id, update_data)
            if result:
                st.success("Empty driving updated successfully")
                st.session_state.route_data = result
                st.rerun()
            else:
                st.error("Failed to update empty driving")

def render_route_optimization(route_id: str):
    """Route optimization interface."""
    st.subheader("Route Optimization")
    
    with st.form("optimization_form"):
        st.write("Optimization Parameters")
        
        optimization_type = st.selectbox(
            "Optimization Goal",
            ["MINIMIZE_COST", "MINIMIZE_TIME", "MINIMIZE_DISTANCE", "BALANCED"],
            help="What aspect of the route should be optimized?"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_stops = st.number_input(
                "Maximum Stops",
                min_value=1,
                value=3,
                help="Maximum number of rest stops"
            )
            
            prefer_highways = st.checkbox(
                "Prefer Highways",
                value=True,
                help="Prioritize highway routes when possible"
            )
        
        with col2:
            avoid_tolls = st.checkbox(
                "Avoid Tolls",
                value=False,
                help="Try to minimize toll costs"
            )
            
            allow_night_driving = st.checkbox(
                "Allow Night Driving",
                value=True,
                help="Include night hours in route planning"
            )
        
        if st.form_submit_button("Optimize Route"):
            optimization_params = {
                "optimization_type": optimization_type,
                "max_stops": max_stops,
                "prefer_highways": prefer_highways,
                "avoid_tolls": avoid_tolls,
                "allow_night_driving": allow_night_driving
            }
            
            with st.spinner("Optimizing route..."):
                result = optimize_route(route_id, optimization_params)
                if result:
                    st.success("Route optimized successfully")
                    # Show optimization results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Cost Savings",
                            format_currency(result.get('cost_savings', 0)),
                            help="Potential cost savings with optimized route"
                        )
                    with col2:
                        st.metric(
                            "Time Saved",
                            f"{result.get('time_saved', 0)} hours",
                            help="Potential time savings with optimized route"
                        )
                    with col3:
                        st.metric(
                            "Distance Reduced",
                            f"{result.get('distance_saved', 0)} km",
                            help="Potential distance reduction with optimized route"
                        )
                    
                    # Option to apply optimization
                    if st.button("Apply Optimized Route"):
                        st.session_state.route_data = result.get('optimized_route')
                        st.rerun()
                else:
                    st.error("Failed to optimize route")

def render_timeline_management(route_id: str):
    """Timeline management interface."""
    st.subheader("Timeline Management")
    
    # Get current timeline
    timeline_data = get_route_timeline(route_id)
    if not timeline_data:
        st.error("Failed to load timeline data")
        return
    
    # Display current timeline
    display_timeline_events(timeline_data['timeline_events'])
    
    # Timeline editing
    st.write("---")
    st.subheader("Edit Timeline")
    
    if st.button("Add Event"):
        if 'editing_events' not in st.session_state:
            st.session_state.editing_events = timeline_data['timeline_events'].copy()
        st.session_state.editing_events.append({
            'location_id': '',
            'type': 'rest',
            'planned_time': datetime.now().isoformat(),
            'duration_hours': 1.0,
            'event_order': len(st.session_state.editing_events)
        })
    
    if hasattr(st.session_state, 'editing_events'):
        edited_events = []
        for idx, event in enumerate(st.session_state.editing_events):
            with st.expander(f"Event {idx + 1}"):
                event_type = st.selectbox(
                    "Event Type",
                    ["pickup", "delivery", "rest"],
                    index=["pickup", "delivery", "rest"].index(event['type']),
                    key=f"type_{idx}"
                )
                
                location_id = st.text_input(
                    "Location ID",
                    value=event['location_id'],
                    key=f"location_{idx}"
                )
                
                planned_time = st.datetime_input(
                    "Planned Time",
                    value=datetime.fromisoformat(event['planned_time'].replace('Z', '+00:00')),
                    key=f"time_{idx}"
                )
                
                duration = st.number_input(
                    "Duration (hours)",
                    min_value=0.5,
                    max_value=24.0,
                    value=float(event['duration_hours']),
                    step=0.5,
                    key=f"duration_{idx}"
                )
                
                if st.button("Remove Event", key=f"remove_{idx}"):
                    continue
                
                edited_events.append({
                    'location_id': location_id,
                    'type': event_type,
                    'planned_time': planned_time.isoformat(),
                    'duration_hours': duration,
                    'event_order': idx
                })
        
        if st.button("Save Timeline"):
            if all(validate_timeline_event(event) for event in edited_events):
                result = update_route_timeline(route_id, edited_events)
                if result:
                    st.success("Timeline updated successfully")
                    del st.session_state.editing_events
                    st.rerun()
                else:
                    st.error("Failed to update timeline")
            else:
                st.error("Please fill in all required fields for each event")

def render_route_segments(route_id: str):
    """Route segments information interface."""
    segments_data = get_route_segments(route_id)
    if segments_data:
        display_route_segments(segments_data['segments'])
    else:
        st.error("Failed to load route segments")

def render_status_management(route_id: str):
    """Status management interface."""
    st.subheader("Status Management")
    
    # Status update section
    cols = st.columns([2, 1])
    with cols[0]:
        new_status = st.selectbox(
            "Update Status",
            ["draft", "planned", "in_progress", "completed", "cancelled"]
        )
        comment = st.text_area("Status Update Comment")
    
    with cols[1]:
        if st.button("Update Status"):
            result = update_route_status(route_id, new_status, comment)
            if result:
                st.success("Status updated successfully")
                st.rerun()
            else:
                st.error("Failed to update status")
    
    # Display status history
    st.write("---")
    history = get_route_status_history(route_id)
    if history:
        display_route_status_history(history)
    else:
        st.info("No status history available") 