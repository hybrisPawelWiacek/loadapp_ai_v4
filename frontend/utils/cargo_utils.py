import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from .shared_utils import api_request, format_currency

def create_cargo(data: Dict) -> Optional[Dict]:
    """Create a new cargo entry."""
    return api_request("/api/cargo", method="POST", data=data)

def get_cargo(cargo_id: str) -> Optional[Dict]:
    """Get cargo details by ID."""
    return api_request(f"/api/cargo/{cargo_id}")

def list_cargo(page: int = 1, size: int = 10, business_entity_id: Optional[str] = None) -> Optional[Dict]:
    """List cargo entries with pagination."""
    params = {
        "page": page,
        "size": size
    }
    if business_entity_id:
        params["business_entity_id"] = business_entity_id
    return api_request("/api/cargo", method="GET", data=params)

def update_cargo(cargo_id: str, data: Dict) -> Optional[Dict]:
    """Update cargo details."""
    return api_request(f"/api/cargo/{cargo_id}", method="PUT", data=data)

def delete_cargo(cargo_id: str) -> bool:
    """Delete a cargo entry."""
    response = api_request(f"/api/cargo/{cargo_id}", method="DELETE")
    # For successful deletion, the API returns a 204 status code
    # The response will be None in this case
    return response is None

def get_cargo_status_history(cargo_id: str) -> Optional[Dict]:
    """Get cargo status history."""
    return api_request(f"/api/cargo/{cargo_id}/status-history")

def display_cargo_details(cargo: Dict):
    """Display cargo details in a formatted way."""
    st.subheader("Cargo Details")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Weight", f"{cargo['weight']} kg")
        st.metric("Value", format_currency(float(cargo['value'])))
        st.metric("Status", cargo['status'].upper())
    
    with col2:
        st.metric("Volume", f"{cargo['volume']} m³")
        st.metric("Type", cargo['cargo_type'].title())
        if cargo.get('special_requirements'):
            st.write("Special Requirements:")
            for req in cargo['special_requirements']:
                st.write(f"- {req}")

def display_cargo_history(history: Dict):
    """Display cargo status history in a timeline format."""
    st.subheader("Status History")
    
    for entry in history.get('history', []):
        with st.expander(f"Status: {entry['new_status']} - {entry['timestamp']}"):
            st.write(f"Previous Status: {entry['old_status']}")
            if entry.get('trigger'):
                st.write(f"Trigger: {entry['trigger']}")
            if entry.get('details'):
                st.write("Details:", entry['details']) 