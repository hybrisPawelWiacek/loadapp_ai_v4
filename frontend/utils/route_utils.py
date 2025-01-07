from typing import Dict, Optional, List
from .shared_utils import api_request

def check_route_feasibility(route_id: str) -> Optional[Dict]:
    """Check if a route is feasible and get validation details."""
    return api_request(f"/api/route/check-feasibility/{route_id}")

def get_alternative_routes(route_id: str) -> Optional[List[Dict]]:
    """Get alternative route suggestions."""
    return api_request(f"/api/route/{route_id}/alternatives")

def optimize_route(route_id: str, optimization_params: Dict) -> Optional[Dict]:
    """Request route optimization with specific parameters."""
    return api_request(
        f"/api/route/{route_id}/optimize",
        method="POST",
        data=optimization_params
    )

def get_route_timeline(route_id: str) -> Optional[Dict]:
    """Get timeline events for a route."""
    return api_request(f"/api/route/{route_id}/timeline")

def update_route_timeline(route_id: str, events: List[Dict]) -> Optional[Dict]:
    """Update timeline events for a route."""
    return api_request(
        f"/api/route/{route_id}/timeline",
        method="PUT",
        data={"timeline_events": events}
    )

def get_route_segments(route_id: str) -> Optional[Dict]:
    """Get route segments information."""
    return api_request(f"/api/route/{route_id}/segments")

def get_route_status_history(route_id: str) -> Optional[Dict]:
    """Get route status history."""
    return api_request(f"/api/route/{route_id}/status-history")

def update_route_status(route_id: str, status: str, comment: str = "") -> Optional[Dict]:
    """Update route status."""
    return api_request(
        f"/api/route/{route_id}/status",
        method="PUT",
        data={"status": status, "comment": comment}
    )

def display_timeline_events(events: List[Dict]):
    """Display timeline events in a formatted way."""
    import streamlit as st
    
    st.subheader("Timeline Events")
    for event in events:
        with st.expander(f"{event['type'].title()} - {event['planned_time']}"):
            st.write(f"Location: {event['location'].get('address', 'N/A')}")
            st.write(f"Duration: {event['duration_hours']} hours")
            st.write(f"Order: {event['event_order']}")

def display_route_segments(segments: List[Dict]):
    """Display route segments in a formatted way."""
    import streamlit as st
    
    st.subheader("Route Segments")
    for segment in segments:
        segment_type = segment.get('type', 'route')
        if segment_type == 'empty_driving':
            with st.expander("Segment - Empty Driving", expanded=True):
                st.metric("Distance", segment['distance_formatted'])
                st.metric("Duration", segment['duration_formatted'])
                st.write(f"From: {segment['start_location']['address']}")
                st.write(f"To: {segment['end_location']['address']}")
        else:  # route segment
            with st.expander(f"Segment - {segment['country_code']}", expanded=True):
                st.metric("Distance", segment['distance_formatted'])
                st.metric("Duration", segment['duration_formatted'])
                st.write(f"From: {segment['start_location']['address']}")
                st.write(f"To: {segment['end_location']['address']}")

def display_route_status_history(history: List[Dict]):
    """Display route status history in a formatted way."""
    import streamlit as st
    
    for entry in history:
        with st.expander(f"Status: {entry['status']} - {entry['timestamp']}"):
            if entry.get('comment'):
                st.write(f"Comment: {entry['comment']}")

def validate_timeline_event(event: Dict) -> bool:
    """Validate timeline event data."""
    required_fields = ['location_id', 'type', 'planned_time', 'duration_hours']
    return all(field in event and event[field] for field in required_fields) 