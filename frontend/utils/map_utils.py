import folium
from typing import Dict, List, Tuple, Any
import polyline

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

EMPTY_DRIVING_COLOR = '#28a745'  # Green

def create_route_map(route_data: Dict) -> folium.Map:
    """Create a simple route map with polylines and markers."""
    # Default center coordinates (roughly center of Germany)
    default_center = (52.0, 13.0)
    
    try:
        print("DEBUG - Route data structure:", {
            'has_empty_driving': bool(route_data.get('empty_driving')),
            'country_segments_count': len(route_data.get('country_segments', [])),
            'timeline_events_count': len(route_data.get('timeline_events', []))
        })
        
        # Create base map
        m = folium.Map(location=default_center, zoom_start=6)
        
        # Draw empty driving segment
        empty_driving = route_data.get('empty_driving', {})
        if empty_driving:
            print("DEBUG - Empty driving data:", {
                'has_start_loc': bool(empty_driving.get('start_location')),
                'has_end_loc': bool(empty_driving.get('end_location')),
                'route_points_count': len(empty_driving.get('route_points', [])),
                'route_points_sample': empty_driving.get('route_points', [])[:2] if empty_driving.get('route_points') else None
            })
            
            start_loc = empty_driving.get('start_location', {})
            end_loc = empty_driving.get('end_location', {})
            route_points = empty_driving.get('route_points', [])
            
            if start_loc and end_loc:
                # Create coordinates for empty driving
                if route_points:
                    print("DEBUG - Empty driving route points format:", type(route_points[0]), route_points[0] if route_points else None)
                    coordinates = route_points  # Use points directly, they should already be in the right format
                else:
                    coordinates = [
                        [start_loc['latitude'], start_loc['longitude']],
                        [end_loc['latitude'], end_loc['longitude']]
                    ]
                
                # Draw empty driving polyline
                folium.PolyLine(
                    coordinates,
                    weight=3,
                    color=EMPTY_DRIVING_COLOR,
                    opacity=0.8,
                    dash_array='10',
                    tooltip='Empty Driving'
                ).add_to(m)
                
                # Add markers for empty driving with green color
                folium.Marker(
                    [start_loc['latitude'], start_loc['longitude']],
                    popup=f"Empty Start: {start_loc['address']}",
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(m)
                
                folium.Marker(
                    [end_loc['latitude'], end_loc['longitude']],
                    popup=f"Empty End: {end_loc['address']}",
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(m)
        
        # Draw country segments
        for i, segment in enumerate(route_data.get('country_segments', [])):
            print(f"DEBUG - Processing country segment {i}:", {
                'country_code': segment.get('country_code'),
                'has_start_loc': bool(segment.get('start_location')),
                'has_end_loc': bool(segment.get('end_location')),
                'route_points_count': len(segment.get('route_points', [])),
                'route_points_sample': segment.get('route_points', [])[:2] if segment.get('route_points') else None
            })
            
            start_loc = segment.get('start_location', {})
            end_loc = segment.get('end_location', {})
            route_points = segment.get('route_points', [])
            country_code = segment.get('country_code', 'N/A')
            
            if start_loc and end_loc:
                # Create coordinates for segment
                if route_points:
                    print(f"DEBUG - Country segment {i} route points format:", type(route_points[0]), route_points[0] if route_points else None)
                    coordinates = route_points  # Use points directly, they should already be in the right format
                else:
                    coordinates = [
                        [start_loc['latitude'], start_loc['longitude']],
                        [end_loc['latitude'], end_loc['longitude']]
                    ]
                
                # Draw segment polyline
                color = COUNTRY_COLORS.get(country_code, '#000000')
                folium.PolyLine(
                    coordinates,
                    weight=3,
                    color=color,
                    opacity=0.8,
                    tooltip=f'Country: {country_code}'
                ).add_to(m)
                
                # Add country label
                if coordinates:
                    mid_point = coordinates[len(coordinates) // 2]
                    folium.Marker(
                        mid_point,
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 12pt; color: {color}">{country_code}</div>'
                        )
                    ).add_to(m)
                
                # Add markers for segment endpoints with matching timeline event colors
                start_event = next((e for e in route_data.get('timeline_events', []) 
                                  if e.get('location', {}).get('address') == start_loc['address']), None)
                end_event = next((e for e in route_data.get('timeline_events', []) 
                                if e.get('location', {}).get('address') == end_loc['address']), None)
                
                # Start marker
                start_color = _get_folium_color(TIMELINE_COLORS.get(start_event['type'], '#000000')) if start_event else 'blue'
                folium.Marker(
                    [start_loc['latitude'], start_loc['longitude']],
                    popup=f"Start ({country_code}): {start_loc['address']}",
                    icon=folium.Icon(color=start_color, icon='info-sign')
                ).add_to(m)
                
                # End marker
                end_color = _get_folium_color(TIMELINE_COLORS.get(end_event['type'], '#000000')) if end_event else 'blue'
                folium.Marker(
                    [end_loc['latitude'], end_loc['longitude']],
                    popup=f"End ({country_code}): {end_loc['address']}",
                    icon=folium.Icon(color=end_color, icon='info-sign')
                ).add_to(m)
        
        # Add timeline events
        for event in route_data.get('timeline_events', []):
            loc = event.get('location', {})
            if loc and 'latitude' in loc and 'longitude' in loc:
                event_type = event.get('type', '').lower()
                color = _get_folium_color(TIMELINE_COLORS.get(event_type, '#000000'))
                
                # Add marker for timeline event
                folium.Marker(
                    [loc['latitude'], loc['longitude']],
                    popup=f"{event_type.title()}: {loc.get('address', 'N/A')}",
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
                
                # Add circle marker for visual emphasis
                folium.CircleMarker(
                    location=[loc['latitude'], loc['longitude']],
                    radius=8,
                    color=TIMELINE_COLORS.get(event_type, '#000000'),  # Use hex color for circle
                    fill=True,
                    popup=f"{event_type.title()}: {loc.get('address', 'N/A')}",
                    tooltip=f"{event_type.title()}: {loc.get('address', 'N/A')}"
                ).add_to(m)
        
        # Add map legend
        legend_html = """
        <div class="map-legend-container" style="margin: 20px 0;">
            <div class="map-legend" style="
                width: 250px;
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                font-family: sans-serif;
                ">
                <h4 style="margin: 0 0 10px 0; color: #333;">Map Legend</h4>
                
                <p style="margin: 10px 0 5px 0; font-weight: bold; color: #666;">Route Segments:</p>
                <div style="display: flex; align-items: center; margin: 5px 0">
                    <div style="width: 30px; height: 3px; background-color: %s; margin-right: 10px; border-style: dashed;"></div>
                    <span style="color: #333;">Empty Driving</span>
                </div>
        """ % EMPTY_DRIVING_COLOR

        # Add country colors to legend
        for country, color in COUNTRY_COLORS.items():
            legend_html += f"""
                <div style="display: flex; align-items: center; margin: 5px 0">
                    <div style="width: 30px; height: 3px; background-color: {color}; margin-right: 10px;"></div>
                    <span style="color: #333;">{country} Route</span>
                </div>
            """

        # Add timeline event colors to legend
        legend_html += """
                <p style="margin: 15px 0 5px 0; font-weight: bold; color: #666;">Timeline Events:</p>
        """
        for event_type, color in TIMELINE_COLORS.items():
            legend_html += f"""
                <div style="display: flex; align-items: center; margin: 5px 0">
                    <div style="width: 15px; height: 15px; border-radius: 50%; background-color: {color}; margin-right: 10px;"></div>
                    <span style="color: #333;">{event_type.title()}</span>
                </div>
            """

        legend_html += """
            </div>
        </div>
        """

        # Instead of adding to map root, return both map and legend
        return m, legend_html
    except Exception as e:
        print(f"Error creating route map: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return folium.Map(location=default_center, zoom_start=6), "" 

def draw_route_on_map(m: folium.Map, segments: List[Dict], draw_markers: bool = True):
    """Draw route segments on the map."""
    logger.info(f"Drawing {len(segments)} segments on map")
    
    # Colors for different segment types
    colors = {
        "empty_driving": "gray",
        "loaded_driving": "blue",
        "border_crossing": "red"
    }
    
    for i, segment in enumerate(segments):
        try:
            logger.debug(f"Processing segment {i+1}/{len(segments)}", extra={
                'segment_type': segment.get('type'),
                'has_route_points': bool(segment.get('route_points')),
                'route_points_count': len(segment.get('route_points', [])),
                'start_location': segment.get('start_location'),
                'end_location': segment.get('end_location')
            })
            
            # Get segment details
            segment_type = segment.get('type')
            start_location = segment.get('start_location')
            end_location = segment.get('end_location')
            route_points = segment.get('route_points', [])
            
            if not start_location or not end_location:
                logger.error(f"Missing location data for segment {i+1}")
                continue
                
            # Draw markers if requested
            if draw_markers:
                # Start location marker
                folium.Marker(
                    [start_location['latitude'], start_location['longitude']],
                    popup=f"Start: {start_location['address']}",
                    icon=folium.Icon(color='green' if i == 0 else 'blue')
                ).add_to(m)
                
                # End location marker
                folium.Marker(
                    [end_location['latitude'], end_location['longitude']],
                    popup=f"End: {end_location['address']}",
                    icon=folium.Icon(color='red' if i == len(segments)-1 else 'blue')
                ).add_to(m)

            # Draw route line if route points are available
            if route_points:
                logger.debug(f"Drawing polyline for segment {i+1} with {len(route_points)} points")
                # Route points are already in [lat, lng] format, use them directly
                folium.PolyLine(
                    route_points,
                    weight=3,
                    color=colors.get(segment_type, 'blue'),
                    opacity=0.8
                ).add_to(m)
            else:
                logger.warning(f"No route points available for segment {i+1}, drawing straight line")
                # If no route points, draw straight line between start and end
                coordinates = [
                    [start_location['latitude'], start_location['longitude']],
                    [end_location['latitude'], end_location['longitude']]
                ]
                folium.PolyLine(
                    coordinates,
                    weight=3,
                    color=colors.get(segment_type, 'blue'),
                    opacity=0.8,
                    dash_array='10'
                ).add_to(m)
            
            # Add country label if it's a country segment
            if segment.get('country_code'):
                center_lat = (start_location['latitude'] + end_location['latitude']) / 2
                center_lng = (start_location['longitude'] + end_location['longitude']) / 2
                folium.Popup(
                    segment['country_code'],
                    permanent=True
                ).add_to(folium.Marker(
                    [center_lat, center_lng],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size: 12pt; color: black;">{segment["country_code"]}</div>'
                    )
                ).add_to(m))

        except Exception as e:
            logger.error(f"Error processing segment {i+1}: {str(e)}")
            continue
    
    logger.info("Finished drawing route on map") 

# Helper function to convert hex colors to Folium color names
def _get_folium_color(hex_color: str) -> str:
    """Convert hex color to closest Folium color name."""
    color_map = {
        '#28a745': 'green',  # Green for pickup and empty driving
        '#ffc107': 'orange', # Yellow/Orange for rest
        '#dc3545': 'red',    # Red for delivery
        '#000000': 'black'   # Default
    }
    return color_map.get(hex_color, 'blue') 