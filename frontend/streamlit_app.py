import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import folium
from streamlit_folium import folium_static
import pandas as pd

# Configuration
API_URL = "http://127.0.0.1:5001"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'http://localhost:8501'
}

# Constants for visualization
TIMELINE_COLORS = {
    'pickup': '#28a745',    # Green
    'rest': '#ffc107',      # Yellow
    'delivery': '#dc3545'   # Red
}

COUNTRY_COLORS = {
    'DE': '#003399',  # German Blue
    'PL': '#dc143c',  # Polish Red
    'CZ': '#11457e',  # Czech Blue
    'AT': '#ef3340',  # Austrian Red
}

# Add to Configuration section
COST_COMPONENTS = {
    'fuel': 'Fuel Costs',
    'toll': 'Toll Charges',
    'driver': 'Driver Costs',
    'overhead': 'Business Overhead',
    'events': 'Event Costs (loading/unloading)'
}

st.set_page_config(
    page_title="LoadApp.AI - Transport Route Calculator",
    layout="wide",
    initial_sidebar_state="expanded"
)

def fetch_transport_types() -> list:
    """Fetch available transport types from the API."""
    try:
        response = requests.get(
            f"{API_URL}/api/transport/types",
            headers=HEADERS,
            timeout=5
        )
        if response.status_code == 200:
            types = response.json()
            return [(t["id"], t["name"]) for t in types]
        else:
            st.error(f"Failed to fetch transport types: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching transport types: {str(e)}")
        return []

def create_cargo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new cargo entry."""
    try:
        response = requests.post(
            f"{API_URL}/api/cargo",
            headers=HEADERS,
            json=data,
            timeout=5
        )
        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Failed to create cargo: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error creating cargo: {str(e)}")
        return None

def calculate_route(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate route using the provided data."""
    try:
        response = requests.post(
            f"{API_URL}/api/route/calculate",
            headers=HEADERS,
            json=data,
            timeout=10  # Longer timeout for route calculation
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to calculate route: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calculating route: {str(e)}")
        return None

def create_route_map(route: Dict[str, Any]) -> folium.Map:
    """Create a folium map with the route visualization."""
    # Get coordinates for the route
    coordinates = []
    
    # Add origin
    origin = route['timeline_events'][0]['location']
    coordinates.append((origin['latitude'], origin['longitude']))
    
    # Add intermediate points from country segments
    for segment in route['country_segments']:
        coordinates.append((
            segment['start_location']['latitude'],
            segment['start_location']['longitude']
        ))
        coordinates.append((
            segment['end_location']['latitude'],
            segment['end_location']['longitude']
        ))
    
    # Add destination
    destination = route['timeline_events'][-1]['location']
    coordinates.append((destination['latitude'], destination['longitude']))
    
    # Create map centered on the route
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add route line
    folium.PolyLine(
        coordinates,
        weight=3,
        color='blue',
        opacity=0.8
    ).add_to(m)
    
    # Add markers for timeline events
    for event in route['timeline_events']:
        loc = event['location']
        color = TIMELINE_COLORS.get(event['type'].lower(), 'gray')
        
        folium.CircleMarker(
            location=[loc['latitude'], loc['longitude']],
            radius=8,
            color=color,
            fill=True,
            popup=f"{event['type'].title()}: {event['planned_time']}"
        ).add_to(m)
    
    return m

def display_timeline(events: list):
    """Display an interactive timeline of events."""
    st.subheader("Route Timeline")
    
    # Create a DataFrame for better visualization
    timeline_data = []
    for event in events:
        timeline_data.append({
            'Event': event['type'].title(),
            'Time': datetime.fromisoformat(event['planned_time']).strftime('%Y-%m-%d %H:%M'),
            'Duration': f"{event['duration_hours']}h",
            'Location': event['location']['address']
        })
    
    df = pd.DataFrame(timeline_data)
    
    # Display as a styled table
    st.dataframe(
        df,
        column_config={
            "Event": st.column_config.TextColumn(
                "Event Type",
                help="Type of timeline event"
            ),
            "Time": st.column_config.TextColumn(
                "Scheduled Time",
                help="Planned time for the event"
            ),
            "Duration": st.column_config.TextColumn(
                "Duration",
                help="Event duration"
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                help="Event location"
            )
        },
        hide_index=True,
    )

def display_country_segments(segments: list):
    """Display country segments with details."""
    st.subheader("Route Segments")
    
    # Create a DataFrame for better visualization
    segment_data = []
    for segment in segments:
        segment_data.append({
            'Country': segment['country_code'],
            'Distance': f"{segment['distance_km']:.1f} km",
            'Duration': f"{segment['duration_hours']:.1f}h",
            'From': segment['start_location']['address'],
            'To': segment['end_location']['address']
        })
    
    df = pd.DataFrame(segment_data)
    
    # Display as a styled table
    st.dataframe(
        df,
        column_config={
            "Country": st.column_config.TextColumn(
                "Country",
                help="Country code"
            ),
            "Distance": st.column_config.TextColumn(
                "Distance",
                help="Segment distance"
            ),
            "Duration": st.column_config.TextColumn(
                "Duration",
                help="Segment duration"
            ),
            "From": st.column_config.TextColumn(
                "From",
                help="Start location"
            ),
            "To": st.column_config.TextColumn(
                "To",
                help="End location"
            )
        },
        hide_index=True,
    )

def create_cost_settings(route_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create cost settings for a route."""
    try:
        response = requests.post(
            f"{API_URL}/api/cost/settings/{route_id}",
            headers=HEADERS,
            json=data,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to create cost settings: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error creating cost settings: {str(e)}")
        return None

def calculate_costs(route_id: str) -> Dict[str, Any]:
    """Calculate costs for a route."""
    try:
        response = requests.post(
            f"{API_URL}/api/cost/calculate/{route_id}",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to calculate costs: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calculating costs: {str(e)}")
        return None

def display_cost_settings(route_id: str) -> Dict[str, Any]:
    """Display and configure cost settings."""
    st.subheader("Cost Settings")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Enable/disable cost components
        st.write("Enable Cost Components:")
        enabled_components = []
        for comp_id, comp_name in COST_COMPONENTS.items():
            if st.checkbox(comp_name, value=True, key=f"cost_comp_{comp_id}"):
                enabled_components.append(comp_id)
    
    with col2:
        # Configure rates
        st.write("Configure Rates:")
        rates = {}
        rates['fuel_rate'] = st.number_input("Fuel Rate (EUR/L)", value=1.5, step=0.1)
        rates['event_rate'] = st.number_input("Event Rate (EUR/hour)", value=50.0, step=5.0)
    
    # Create/update cost settings
    if st.button("Save Cost Settings"):
        settings_data = {
            "enabled_components": enabled_components,
            "rates": rates
        }
        settings = create_cost_settings(route_id, settings_data)
        if settings:
            st.success("Cost settings saved successfully!")
            return settings
    
    return None

def display_cost_breakdown(breakdown: Dict[str, Any]):
    """Display cost breakdown details."""
    st.subheader("Cost Breakdown")
    
    # Create columns for summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"€{float(breakdown['total_cost']):.2f}")
    with col2:
        total_fuel = sum(float(v) for v in breakdown['fuel_costs'].values())
        st.metric("Total Fuel Cost", f"€{total_fuel:.2f}")
    with col3:
        total_toll = sum(float(v) for v in breakdown['toll_costs'].values())
        st.metric("Total Toll Cost", f"€{total_toll:.2f}")
    
    # Detailed breakdowns in expandable sections
    with st.expander("Fuel Costs by Country"):
        for country, cost in breakdown['fuel_costs'].items():
            st.write(f"{country}: €{float(cost):.2f}")
    
    with st.expander("Toll Costs by Country"):
        for country, cost in breakdown['toll_costs'].items():
            st.write(f"{country}: €{float(cost):.2f}")
    
    with st.expander("Other Costs"):
        st.write(f"Driver Costs: €{float(breakdown['driver_costs']):.2f}")
        st.write(f"Overhead Costs: €{float(breakdown['overhead_costs']):.2f}")
        for event_type, cost in breakdown['timeline_event_costs'].items():
            st.write(f"{event_type.title()} Event Cost: €{float(cost):.2f}")

def generate_offer(route_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an offer for the route."""
    try:
        response = requests.post(
            f"{API_URL}/api/offer/generate/{route_id}",
            headers=HEADERS,
            json=data,
            timeout=15  # Longer timeout for AI content generation
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to generate offer: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error generating offer: {str(e)}")
        return None

def display_offer(offer: Dict[str, Any], route: Dict[str, Any], costs: Dict[str, Any]):
    """Display the generated offer with enhanced content."""
    st.subheader("Transport Offer")
    
    # Price presentation
    col1, col2, col3 = st.columns(3)
    with col1:
        base_cost = float(costs['breakdown']['total_cost'])
        st.metric("Base Cost", f"€{base_cost:.2f}")
    with col2:
        margin = float(offer['margin_percentage'])
        st.metric("Margin", f"{margin:.1f}%")
    with col3:
        final_price = float(offer['final_price'])
        st.metric("Final Price", f"€{final_price:.2f}", 
                 delta=f"€{(final_price - base_cost):.2f}")
    
    # Offer content in styled container
    st.markdown("---")
    with st.container():
        # Title and description
        st.markdown(f"### {offer['content']['title']}")
        st.markdown(offer['content']['description'])
        
        # Key highlights
        st.markdown("#### Key Highlights")
        for highlight in offer['content']['highlights']:
            st.markdown(f"- {highlight}")
        
        # Terms and conditions
        with st.expander("Terms & Conditions"):
            for term in offer['content']['terms']:
                st.markdown(f"- {term}")
    
    # Fun fact in a styled box
    if offer.get('fun_fact'):
        st.markdown("---")
        st.info(f"🎯 **Did you know?** {offer['fun_fact']}")

def display_route(route: Dict[str, Any]):
    """Display the calculated route details."""
    if not route:
        return

    st.success("Route calculated successfully!")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Map View", "Timeline", "Segments", "Costs", "Offer"])
    
    with tab1:
        # Display map
        st.subheader("Route Map")
        route_map = create_route_map(route)
        folium_static(route_map, width=1200, height=600)
        
        # Basic metrics below the map
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Distance", f"{route['total_distance_km']:.1f} km")
        with col2:
            st.metric("Total Duration", f"{route['total_duration_hours']:.1f} hours")
        with col3:
            st.metric("Countries", len(set(seg['country_code'] for seg in route['country_segments'])))
    
    with tab2:
        # Display timeline
        display_timeline(route['timeline_events'])
    
    with tab3:
        # Display country segments
        display_country_segments(route['country_segments'])
    
    with tab4:
        # Cost Management Section
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Cost Settings
            settings = display_cost_settings(route['id'])
        
        with col2:
            # Calculate and display costs if settings exist
            if settings or st.button("Calculate Costs"):
                costs = calculate_costs(route['id'])
                if costs:
                    display_cost_breakdown(costs['breakdown'])
                    
                    # Store costs in session state for offer generation
                    st.session_state.current_costs = costs
    
    with tab5:
        # Offer Generation and Display
        if hasattr(st.session_state, 'current_costs'):
            st.subheader("Generate Transport Offer")
            
            # Offer configuration
            margin_percentage = st.slider(
                "Margin Percentage",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                help="Set the profit margin for this transport"
            )
            
            if st.button("Generate Offer"):
                offer_data = {
                    "margin_percentage": margin_percentage,
                    "cost_breakdown_id": st.session_state.current_costs['breakdown']['id']
                }
                
                offer = generate_offer(route['id'], offer_data)
                if offer:
                    display_offer(offer, route, st.session_state.current_costs)
        else:
            st.warning("Please calculate costs first before generating an offer.")

def main():
    st.title("LoadApp.AI - Transport Route Calculator")
    
    # Fetch transport types for the dropdown
    transport_types = fetch_transport_types()
    if not transport_types:
        st.warning("No transport types available. Please check the backend connection.")
        return

    with st.form("transport_input"):
        # 1. Transport Selection
        transport_type = st.selectbox(
            "Transport Type",
            options=[t[0] for t in transport_types],
            format_func=lambda x: dict(transport_types)[x]
        )
        
        # 2. Location Input
        st.subheader("Route Details")
        origin = st.text_input("Origin Address")
        destination = st.text_input("Destination Address")
        
        # 3. Time Selection
        col1, col2 = st.columns(2)
        with col1:
            st.write("Pickup Time")
            pickup_date = st.date_input("Pickup Date")
            pickup_time = st.time_input("Pickup Time")
        with col2:
            st.write("Delivery Time")
            delivery_date = st.date_input(
                "Delivery Date",
                value=pickup_date + timedelta(days=1)
            )
            delivery_time = st.time_input("Delivery Time")
        
        # 4. Cargo Details
        st.subheader("Cargo Details")
        col1, col2 = st.columns(2)
        with col1:
            cargo_weight = st.number_input("Weight (kg)", min_value=0.0)
            cargo_value = st.number_input("Value (EUR)", min_value=0.0)
        with col2:
            special_requirements = st.multiselect(
                "Special Requirements",
                ["Temperature Controlled", "Fragile", "Hazardous"]
            )
        
        submit = st.form_submit_button("Calculate Route")
    
    if submit:
        # Validate inputs
        if not all([origin, destination, cargo_weight > 0, cargo_value > 0]):
            st.error("Please fill in all required fields")
            return
        
        # Create cargo first
        cargo_data = {
            "weight": cargo_weight,
            "value": str(cargo_value),
            "special_requirements": special_requirements
        }
        cargo = create_cargo(cargo_data)
        if not cargo:
            return
        
        # Calculate route
        route_data = {
            "transport_id": transport_type,
            "cargo_id": cargo["id"],
            "origin": origin,
            "destination": destination,
            "pickup_time": datetime.combine(pickup_date, pickup_time).isoformat(),
            "delivery_time": datetime.combine(delivery_date, delivery_time).isoformat()
        }
        
        route = calculate_route(route_data)
        if route:
            display_route(route)

if __name__ == "__main__":
    main()
