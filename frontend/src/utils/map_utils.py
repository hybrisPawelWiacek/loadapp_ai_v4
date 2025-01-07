from typing import List, Dict
import folium
import logging

logger = logging.getLogger(__name__)

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
                coordinates = [[point['lat'], point['lng']] for point in route_points]
                folium.PolyLine(
                    coordinates,
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