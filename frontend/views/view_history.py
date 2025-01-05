import streamlit as st
import pandas as pd
import pickle
from datetime import datetime
from utils.shared_utils import ROUTE_HISTORY_FILE, format_currency
from utils.map_utils import create_route_map
from streamlit_folium import folium_static

def load_history() -> list:
    """Load history from cache file."""
    if not ROUTE_HISTORY_FILE.exists():
        return []
    
    try:
        with open(ROUTE_HISTORY_FILE, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")
        return []

def display_history_table(history: list):
    """Display route and offer history as a table."""
    if not history:
        st.info("No history available yet")
        return
    
    st.subheader("Route History")
    
    # Create DataFrame for better display
    history_data = []
    for entry in history:
        route = entry['route']
        costs = entry['costs']
        offer = entry['offer']
        
        history_data.append({
            'Date': datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M'),
            'Route': f"{route['timeline_events'][0]['location']['address']} → {route['timeline_events'][-1]['location']['address']}",
            'Distance': f"{route['total_distance_km']:.1f} km",
            'Cost': format_currency(float(costs['breakdown']['total_cost'])),
            'Price': format_currency(float(offer['final_price'])) if offer else 'N/A'
        })
    
    df = pd.DataFrame(history_data)
    st.dataframe(
        df,
        column_config={
            "Date": st.column_config.TextColumn(
                "Date",
                help="When the route was calculated"
            ),
            "Route": st.column_config.TextColumn(
                "Route",
                help="Origin to destination"
            ),
            "Distance": st.column_config.TextColumn(
                "Distance",
                help="Total route distance"
            ),
            "Cost": st.column_config.TextColumn(
                "Base Cost",
                help="Total calculated cost"
            ),
            "Price": st.column_config.TextColumn(
                "Offer Price",
                help="Final offer price"
            )
        },
        hide_index=True,
        use_container_width=True
    )

def display_history_details(history: list):
    """Display detailed history with expandable entries."""
    for idx, entry in enumerate(history):
        route = entry['route']
        costs = entry['costs']
        offer = entry['offer']
        
        with st.expander(f"Route {idx + 1}: {route['timeline_events'][0]['location']['address']} → {route['timeline_events'][-1]['location']['address']}"):
            # Route details tab
            tab1, tab2, tab3 = st.tabs(["Route Details", "Cost Breakdown", "Offer"])
            
            with tab1:
                # Display route map
                st.subheader("Route Map")
                route_map = create_route_map(route)
                folium_static(route_map, width=800, height=400)
                
                # Route metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Distance", f"{route['total_distance_km']:.1f} km")
                with col2:
                    st.metric("Duration", f"{route['total_duration_hours']:.1f}h")
                with col3:
                    countries = len(set(seg['country_code'] for seg in route['country_segments']))
                    st.metric("Countries", str(countries))
            
            with tab2:
                # Cost breakdown
                st.subheader("Cost Breakdown")
                breakdown = costs['breakdown']
                
                # Summary metrics
                total_cost = float(breakdown['total_cost'])
                total_fuel = sum(float(v) for v in breakdown['fuel_costs'].values())
                total_toll = sum(float(v) for v in breakdown['toll_costs'].values())
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Cost", format_currency(total_cost))
                with col2:
                    st.metric("Fuel Cost", format_currency(total_fuel))
                with col3:
                    st.metric("Toll Cost", format_currency(total_toll))
            
            with tab3:
                # Offer details
                st.subheader("Offer Details")
                if offer:
                    st.markdown(f"### {offer['content']['title']}")
                    st.markdown(offer['content']['description'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Base Cost", format_currency(total_cost))
                    with col2:
                        st.metric("Final Price", format_currency(float(offer['final_price'])))
                    
                    with st.expander("Key Highlights"):
                        for highlight in offer['content']['highlights']:
                            st.markdown(f"• {highlight}")
                    
                    if offer.get('fun_fact'):
                        st.info(f"🎯 **Did you know?** {offer['fun_fact']}")
                else:
                    st.info("No offer generated for this route")

def display_history():
    """Display the complete history view."""
    st.title("Route History")
    
    history = load_history()
    if not history:
        st.info("No routes in history yet. Complete a route calculation to see it here.")
        return
    
    # Display options
    view_type = st.radio(
        "Select View",
        ["Table View", "Detailed View"],
        horizontal=True
    )
    
    if view_type == "Table View":
        display_history_table(history)
    else:
        display_history_details(history)
    
    # Export options
    if st.button("Export All History"):
        # Create DataFrame for export
        export_data = []
        for entry in history:
            route = entry['route']
            costs = entry['costs']
            offer = entry['offer']
            
            export_data.append({
                'Date': datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M'),
                'Origin': route['timeline_events'][0]['location']['address'],
                'Destination': route['timeline_events'][-1]['location']['address'],
                'Distance (km)': route['total_distance_km'],
                'Duration (hours)': route['total_duration_hours'],
                'Base Cost': costs['breakdown']['total_cost'],
                'Final Price': offer['final_price'] if offer else None
            })
        
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download History (CSV)",
            data=csv,
            file_name="route_history.csv",
            mime="text/csv"
        ) 