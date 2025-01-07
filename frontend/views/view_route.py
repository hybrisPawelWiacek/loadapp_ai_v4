import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.shared_utils import format_currency, API_BASE_URL
from utils.route_utils import (
    get_route_timeline, update_route_timeline,
    get_route_segments, get_route_status_history,
    update_route_status, display_timeline_events,
    display_route_segments, display_route_status_history,
    validate_timeline_event, check_route_feasibility,
    optimize_route, update_empty_driving
)
from utils.map_utils import (
    create_route_map,
    EMPTY_DRIVING_COLOR,
    COUNTRY_COLOR_PALETTE,
    TIMELINE_COLORS
)
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import requests

def _format_distance(distance_km: float) -> str:
    """Format distance in kilometers to a user-friendly string."""
    return f"{round(distance_km, 1)} km"

def _format_duration(duration_hours: float) -> str:
    """Convert decimal hours to a user-friendly hours and minutes format."""
    total_minutes = int(duration_hours * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours == 0:
        return f"{minutes}min"
    return f"{hours}h {minutes}min"

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
        "Optimization"
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
    
    # Add navigation button at the bottom
    st.write("---")
    if st.button("💰 Proceed to Cost Management", type="primary", use_container_width=True):
        st.session_state.should_navigate_to_cost = True
        st.rerun()

def render_route_overview(route_data: Dict):
    """Enhanced route overview with feasibility check."""
    st.subheader("Route Overview")
    
    # Basic metrics
    col1, col2, col3 = st.columns(3)
    
    # Format total distance and duration
    total_distance = _format_distance(route_data.get('total_distance_km', 0))
    total_duration = _format_duration(route_data.get('total_duration_hours', 0))
    
    # Display metrics directly on column objects
    col1.metric(
        "Total Distance",
        total_distance,
        help="Total distance including empty driving"
    )
    
    col2.metric(
        "Total Duration",
        total_duration,
        help="Total duration including stops"
    )
    
    col3.metric(
        "Status",
        route_data.get('status', 'NEW'),
        help="Current route status"
    )
    
    # Feasibility check using data from route response
    with st.expander("Route Feasibility", expanded=False):
        is_feasible = route_data.get('is_feasible', False)
        validations = route_data.get('validations', {})
        
        if is_feasible:
            st.success("✅ Route is feasible")
        else:
            st.warning("⚠️ Route may not be feasible")
        
        # Display validation details
        st.subheader("Validation Details")
        if validations:
            for check, result in validations.items():
                if result:
                    st.success(f"✓ {check.replace('_', ' ').title()}")
                else:
                    st.error(f"✗ {check.replace('_', ' ').title()}")
    
    # Display route map
    st.subheader("Route Map")
    
    # Get segments data from the route segments endpoint for the most up-to-date data
    segments_data = get_route_segments(route_data['id'])
    if segments_data:
        map_data = {
            'timeline_events': route_data.get('timeline_events', []),
            'country_segments': [s for s in segments_data['segments'] if s['type'] != 'empty_driving'],
            'empty_driving': next((s for s in segments_data['segments'] if s['type'] == 'empty_driving'), None)
        }
        route_map, legend_html = create_route_map(map_data)
        
        # Create a container for the map with full width
        st.markdown('''
            <style>
                .element-container iframe { width: 100% !important; }
                div[data-testid="stExpander"] { width: 100%; }
            </style>
        ''', unsafe_allow_html=True)
        
        # Display map with full width using a container
        with st.container():
            folium_static(route_map, height=600)
        
        # Add legend using Streamlit components
        st.subheader("Map Legend")
        
        # Create a container for the legend with a light background
        with st.container():
            # Style the legend container
            st.markdown('''
                <style>
                    div[data-testid="stVerticalBlock"] > div:has(div.legend-item) {
                        background-color: white;
                        padding: 20px;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        max-width: 800px;
                        margin: 0 auto;
                    }
                </style>
            ''', unsafe_allow_html=True)
            
            # Create three columns for the legend
            col1, col2, col3 = st.columns(3)
            
            # Column 1: Route Segments
            with col1:
                st.markdown("##### Route Segments")
                
                # Empty Driving
                if map_data['empty_driving']:
                    empty_driving = map_data['empty_driving']
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.markdown(f'''
                            <div style="background-color: {EMPTY_DRIVING_COLOR}; height: 3px; margin-top: 12px; border-style: dashed;"></div>
                        ''', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"Empty Driving ({_format_distance(empty_driving.get('distance_km', 0))})")
                
                # Country Routes
                present_countries = {segment['country_code'] for segment in map_data['country_segments']}
                country_colors = {}
                for i, country in enumerate(present_countries):
                    segments = [s for s in map_data['country_segments'] if s['country_code'] == country]
                    total_distance = sum(s.get('distance_km', 0) for s in segments)
                    color_idx = i % len(COUNTRY_COLOR_PALETTE)
                    country_colors[country] = COUNTRY_COLOR_PALETTE[color_idx]
                    
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.markdown(f'''
                            <div style="background-color: {country_colors[country]}; height: 3px; margin-top: 12px;"></div>
                        ''', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"{country} Route ({_format_distance(total_distance)})")
            
            # Column 2: Timeline Events
            with col2:
                st.markdown("##### Timeline Events")
                
                # Get timeline events
                timeline_events = route_data.get('timeline_events', [])
                event_times = {event['type']: event['planned_time'] for event in timeline_events}
                
                # Event types with timestamps
                for event_type, color in TIMELINE_COLORS.items():
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.markdown(f'''
                            <div style="
                                width: 15px;
                                height: 15px;
                                border-radius: 50%;
                                background-color: {color};
                                margin: 8px auto;
                            "></div>
                        ''', unsafe_allow_html=True)
                    with c2:
                        timestamp = event_times.get(event_type)
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = dt.strftime("%Y/%m/%d %H:%M")
                            st.markdown(f"{event_type.title()} ({formatted_time})")
                        else:
                            st.markdown(event_type.title())
            
            # Column 3: Location Pins
            with col3:
                st.markdown("##### Location Pins")
                
                # Calculate travel times from truck location
                timeline_events = sorted(route_data.get('timeline_events', []), key=lambda x: x['event_order'])
                total_duration = 0
                
                # Truck Location (start)
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.markdown('''
                        <div style="text-align: center; margin-top: 8px;">
                            <span style="font-size: 20px;">📍</span>
                        </div>
                    ''', unsafe_allow_html=True)
                with c2:
                    st.markdown("Truck Location (0h)")
                
                # Calculate cumulative duration for each event
                event_durations = {}
                current_duration = 0
                
                for event in timeline_events:
                    event_type = event['type']
                    if event_type == 'pickup':
                        # Add empty driving duration for pickup
                        if map_data['empty_driving']:
                            current_duration += map_data['empty_driving'].get('duration_hours', 0)
                    elif event_type == 'rest' or event_type == 'delivery':
                        # For rest and delivery, add all segment durations up to this point
                        current_event_order = event['event_order']
                        # Add durations of all segments before this event
                        for segment in map_data['country_segments']:
                            current_duration += segment.get('duration_hours', 0)
                    
                    event_durations[event_type] = current_duration
                
                # Display locations with travel times
                event_types = {'pickup': ('green', 'Pickup Location'),
                             'rest': ('orange', 'Rest Location'),
                             'delivery': ('red', 'Delivery Location')}
                
                for event_type, (color, label) in event_types.items():
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.markdown(f'''
                            <div style="text-align: center; margin-top: 8px;">
                                <span style="color: {color}; font-size: 20px;">📍</span>
                            </div>
                        ''', unsafe_allow_html=True)
                    with c2:
                        duration = event_durations.get(event_type, 0)
                        st.markdown(f"{label} ({_format_duration(duration)})")
    else:
        st.error("Failed to load route segments for map visualization")

def render_empty_driving_management(route_id: str):
    """Empty driving management interface."""
    st.subheader("Empty Driving Management")
    
    route_data = st.session_state.get('route_data', {})
    empty_driving = route_data.get('empty_driving', {})
    if not empty_driving:
        st.info("No empty driving configuration available")
        return
    
    with st.form("empty_driving_form"):
        st.write("Configure Empty Driving")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Start Location",
                value=empty_driving.get('start_location', {}).get('address', ''),
                help="Where the empty driving segment begins",
                disabled=True  # Since this is set during route creation
            )
        
        with col2:
            st.text_input(
                "End Location",
                value=empty_driving.get('end_location', {}).get('address', ''),
                help="Where the empty driving segment ends",
                disabled=True  # Since this is set during route creation
            )
        
        # Display empty driving metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Empty Distance",
                _format_distance(empty_driving.get('distance_km', 0)),
                help="Distance covered during empty driving"
            )
        with col2:
            st.metric(
                "Empty Duration",
                _format_duration(empty_driving.get('duration_hours', 0)),
                help="Time spent during empty driving"
            )
        with col3:
            st.metric(
                "Empty Cost",
                format_currency(empty_driving.get('total_cost', 0)),
                help="Total cost of empty driving"
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
                "start_address": empty_driving.get('start_location', {}).get('address', ''),
                "end_address": empty_driving.get('end_location', {}).get('address', ''),
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
                            _format_duration(result.get('time_saved', 0)),
                            help="Potential time savings with optimized route"
                        )
                    with col3:
                        st.metric(
                            "Distance Reduced",
                            _format_distance(result.get('distance_saved', 0)),
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
    # Display main route segments
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

def calculate_route(transport_id, origin_id, destination_id, cargo_id, pickup_time, delivery_time, truck_location_address):
    try:
        # First create location for truck's current position
        truck_location_response = requests.post(
            f"{API_BASE_URL}/location",
            json={"address": truck_location_address}
        )
        
        if truck_location_response.status_code != 201:
            st.error(f"Failed to create location for truck's current position: {truck_location_response.text}")
            return False
            
        truck_location_data = truck_location_response.json()
        truck_location_id = truck_location_data.get("id")
        
        if not truck_location_id:
            st.error("No truck location ID received from the server")
            return False
        
        # Now calculate route with all locations
        route_request = {
            "transport_id": transport_id,
            "business_entity_id": st.session_state.get("selected_business_id"),
            "cargo_id": cargo_id,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "pickup_time": pickup_time,
            "delivery_time": delivery_time,
            "truck_location_id": truck_location_id
        }
        
        st.write("Debug - Route request:", route_request)  # Debug output
        
        response = requests.post(
            f"{API_BASE_URL}/route/calculate",
            json=route_request
        )
        
        if response.status_code == 200:
            route_data = response.json()
            st.session_state.route_data = route_data["route"]
            return True
        else:
            st.error(f"API request failed: {response.text}")
            return False
            
    except Exception as e:
        st.error(f"Failed to calculate route. Please check if all inputs are valid. Error: {str(e)}")
        return False 