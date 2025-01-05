import folium
from typing import Dict, List, Tuple, Any

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

def create_route_map(route_data: Dict) -> folium.Map:
    """Enhanced route map creation with better empty driving visualization."""
    # Get coordinates for the route
    coordinates = []
    
    # Default center coordinates if we can't calculate from route
    default_center = (52.0, 13.0)  # Roughly center of Germany
    
    try:
        # Add origin if timeline events exist and have valid location
        if route_data.get('timeline_events') and route_data['timeline_events']:
            origin = route_data['timeline_events'][0].get('location', {})
            if isinstance(origin, dict) and 'latitude' in origin and 'longitude' in origin:
                coordinates.append((origin['latitude'], origin['longitude']))
        
        # Add intermediate points from country segments
        if route_data.get('country_segments'):
            for segment in route_data['country_segments']:
                start_loc = segment.get('start_location', {})
                end_loc = segment.get('end_location', {})
                
                if isinstance(start_loc, dict) and 'latitude' in start_loc and 'longitude' in start_loc:
                    coordinates.append((start_loc['latitude'], start_loc['longitude']))
                if isinstance(end_loc, dict) and 'latitude' in end_loc and 'longitude' in end_loc:
                    coordinates.append((end_loc['latitude'], end_loc['longitude']))
        
        # Add destination if timeline events exist and have valid location
        if route_data.get('timeline_events') and len(route_data['timeline_events']) > 1:
            destination = route_data['timeline_events'][-1].get('location', {})
            if isinstance(destination, dict) and 'latitude' in destination and 'longitude' in destination:
                coordinates.append((destination['latitude'], destination['longitude']))
        
        # Create map centered on the route or use default center
        if coordinates:
            center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
            center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        else:
            center_lat, center_lon = default_center
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
        
        # Add route line if we have coordinates
        if len(coordinates) > 1:
            folium.PolyLine(
                coordinates,
                weight=3,
                color='blue',
                opacity=0.8
            ).add_to(m)
        
        # Add markers for timeline events
        if route_data.get('timeline_events'):
            for event in route_data['timeline_events']:
                loc = event.get('location', {})
                if isinstance(loc, dict) and 'latitude' in loc and 'longitude' in loc:
                    color = TIMELINE_COLORS.get(event.get('type', '').lower(), 'gray')
                    folium.CircleMarker(
                        location=[loc['latitude'], loc['longitude']],
                        radius=8,
                        color=color,
                        fill=True,
                        popup=f"{event.get('type', 'Event').title()}: {event.get('planned_time', 'N/A')}"
                    ).add_to(m)
        
        # Add empty driving visualization with more details
        if route_data.get('empty_driving'):
            empty_driving = route_data['empty_driving']
            start_loc = empty_driving.get('start_location', {})
            end_loc = empty_driving.get('end_location', {})
            
            if all(k in start_loc and k in end_loc for k in ['latitude', 'longitude']):
                # Add empty driving polyline
                empty_coords = [
                    (start_loc['latitude'], start_loc['longitude']),
                    (end_loc['latitude'], end_loc['longitude'])
                ]
                
                # Create a more detailed popup for empty driving
                empty_distance = empty_driving.get('distance_km', 0)
                empty_duration = empty_driving.get('duration_hours', 0)
                empty_cost = empty_driving.get('total_cost', 0)
                
                popup_html = f"""
                    <div style='font-size: 12px;'>
                        <b>Empty Driving Segment</b><br>
                        Distance: {empty_distance:.1f} km<br>
                        Duration: {empty_duration:.1f} hours<br>
                        Cost: {format_currency(empty_cost)}
                    </div>
                """
                
                # Add the empty driving line with enhanced styling
                folium.PolyLine(
                    empty_coords,
                    weight=3,
                    color='gray',
                    opacity=0.6,
                    dash_array='10',
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m)
                
                # Add markers for empty driving points
                for loc, label in [(start_loc, "Empty Start"), (end_loc, "Empty End")]:
                    folium.Marker(
                        [loc['latitude'], loc['longitude']],
                        icon=folium.Icon(color='gray', icon='info-sign'),
                        popup=label
                    ).add_to(m)
        
        # Add country segment labels
        if route_data.get('country_segments'):
            for segment in route_data['country_segments']:
                start_loc = segment.get('start_location', {})
                end_loc = segment.get('end_location', {})
                
                if (isinstance(start_loc, dict) and 'latitude' in start_loc and 'longitude' in start_loc and
                    isinstance(end_loc, dict) and 'latitude' in end_loc and 'longitude' in end_loc):
                    mid_lat = (start_loc['latitude'] + end_loc['latitude']) / 2
                    mid_lon = (start_loc['longitude'] + end_loc['longitude']) / 2
                    
                    country_code = segment.get('country_code', 'N/A')
                    distance = segment.get('distance_km', 0)
                    duration = segment.get('duration_hours', 0)
                    
                    folium.Popup(
                        f"Country: {country_code}<br>"
                        f"Distance: {distance:.1f} km<br>"
                        f"Duration: {duration:.1f}h"
                    ).add_to(folium.Marker(
                        location=[mid_lat, mid_lon],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 12pt; color: {COUNTRY_COLORS.get(country_code, "#000")}">'
                                 f'{country_code}</div>'
                        )
                    )).add_to(m)
        
        return m
    except Exception as e:
        # If anything goes wrong, return a default map centered on Germany
        return folium.Map(location=default_center, zoom_start=6) 