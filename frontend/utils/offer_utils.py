import streamlit as st
from typing import Dict, Optional
from datetime import datetime
from .shared_utils import api_request, format_currency

def generate_offer(route_id: str, margin_percentage: float, enhance_with_ai: bool = True) -> Optional[Dict]:
    """Generate an offer for a route."""
    with st.spinner("Generating offer with AI enhancement... This may take up to 30 seconds..."):
        return api_request(
            f"/api/offer/generate/{route_id}",
            method="POST",
            data={
                "margin_percentage": str(margin_percentage),
                "enhance_with_ai": enhance_with_ai
            }
        )

def get_offer(offer_id: str) -> Optional[Dict]:
    """Get offer details by ID."""
    return api_request(f"/api/offer/{offer_id}")

def enhance_offer(offer_id: str) -> Optional[Dict]:
    """Enhance an existing offer with AI-generated content."""
    with st.spinner("Enhancing offer with new AI content... This may take up to 30 seconds..."):
        return api_request(
            f"/api/offer/{offer_id}/enhance",
            method="POST"
        )

def finalize_offer(offer_id: str) -> Optional[Dict]:
    """Finalize an offer."""
    return api_request(f"/api/offer/{offer_id}/finalize", method="POST")

def update_offer_status(offer_id: str, status: str, comment: str = "") -> Optional[Dict]:
    """Update offer status."""
    return api_request(
        f"/api/offer/{offer_id}/status",
        method="PUT",
        data={"status": status, "comment": comment}
    )

def get_offer_status_history(offer_id: str) -> Optional[Dict]:
    """Get offer status history."""
    return api_request(f"/api/offer/{offer_id}/status-history")

def display_offer_details(offer: Dict):
    """Display offer details in a formatted way."""
    print("DEBUG: Entering display_offer_details")
    print(f"DEBUG: Offer data: {offer}")
    
    if not isinstance(offer, dict):
        st.error("Invalid offer data")
        return
    
    # Basic offer information
    col1, col2 = st.columns(2)
    
    # Column 1 metrics
    print("DEBUG: Displaying metrics in column 1")
    if 'final_price' in offer:
        col1.metric("Final Price", format_currency(float(offer['final_price'])))
    if 'status' in offer:
        col1.metric("Status", offer['status'].upper())
    
    # Column 2 metrics
    print("DEBUG: Displaying metrics in column 2")
    if 'margin_percentage' in offer:
        col2.metric("Margin", f"{offer['margin_percentage']}%")
    if 'created_at' in offer:
        col2.metric("Created", offer['created_at'])
    
    # AI-enhanced content
    if offer.get('ai_content'):
        print("DEBUG: Displaying AI content")
        st.markdown("---")
        st.markdown("### AI-Enhanced Content")
        st.markdown(offer['ai_content'])
    
    if offer.get('fun_fact'):
        print("DEBUG: Displaying fun fact")
        st.info(f"Fun Fact: {offer['fun_fact']}")

def display_offer_history(history: list):
    """Display offer status history in a timeline format."""
    st.subheader("Status History")
    
    for entry in history:
        with st.expander(f"Status: {entry['status']} - {entry['timestamp']}"):
            if entry.get('comment'):
                st.write(f"Comment: {entry['comment']}")

def validate_offer_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if the status transition is allowed."""
    allowed_transitions = {
        'DRAFT': ['FINALIZED'],
        'FINALIZED': []  # No transitions allowed from FINALIZED
    }
    return new_status in allowed_transitions.get(current_status, []) 