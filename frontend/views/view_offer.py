import streamlit as st
from typing import Dict, Optional
from utils.offer_utils import (
    generate_offer, get_offer, enhance_offer,
    finalize_offer, update_offer_status,
    get_offer_status_history, display_offer_details,
    display_offer_history, validate_offer_status_transition
)

def render_offer_view():
    """Render the offer generation and management view."""
    print("DEBUG: Entering render_offer_view")
    
    route_data = st.session_state.get('route_data')
    cost_data = st.session_state.get('cost_data')
    print(f"DEBUG: route_data: {route_data}, cost_data: {cost_data}")
    
    if not route_data or not cost_data:
        print("DEBUG: Missing route_data or cost_data")
        st.info("Please complete route planning and cost management first")
        return
    
    st.title("Offer Management")
    
    # Create tabs for different offer aspects
    tab_generate, tab_enhance, tab_status = st.tabs([
        "Generate Offer", "AI Enhancement", "Status Management"
    ])
    
    offer_data = st.session_state.get('offer_data')
    print(f"DEBUG: offer_data: {offer_data}")
    
    with tab_generate:
        render_offer_generation()
    
    with tab_enhance:
        if offer_data:
            render_offer_enhancement()
        else:
            st.info("Please generate an offer first")
    
    with tab_status:
        if offer_data:
            render_offer_status()
        else:
            st.info("Please generate an offer first")

def render_offer_generation():
    """Render offer generation interface."""
    print("DEBUG: Entering render_offer_generation")
    
    offer_data = st.session_state.get('offer_data')
    route_data = st.session_state.get('route_data')
    print(f"DEBUG: offer_data: {offer_data}, route_data: {route_data}")
    
    if not route_data:
        print("DEBUG: No route data available")
        st.error("Route data not available")
        return
    
    if offer_data:
        print("DEBUG: Displaying existing offer")
        display_offer_details(offer_data)
        if st.button("Generate New Offer"):
            st.session_state['offer_data'] = None
            st.rerun()
        return
    
    print("DEBUG: Showing offer generation controls")
    margin = st.slider(
        "Margin Percentage",
        min_value=1.0,
        max_value=50.0,
        value=15.0,
        step=0.5,
        help="Set the profit margin for the offer"
    )
    
    use_ai = st.checkbox(
        "Enhance with AI",
        value=True,
        help="Use AI to enhance the offer with compelling content"
    )
    
    if st.button("Generate Offer", type="primary"):
        route_id = route_data.get('id')
        if not route_id:
            print("DEBUG: Invalid route data - missing ID")
            st.error("Invalid route data")
            return
        
        print(f"DEBUG: Generating offer for route {route_id}")
        result = generate_offer(route_id, margin, use_ai)
        if result:
            st.session_state['offer_data'] = result.get('offer')
            st.success("Offer generated successfully")
            st.rerun()
        else:
            st.error("Failed to generate offer")

def render_offer_enhancement():
    """Render AI enhancement interface."""
    offer_data = st.session_state.get('offer_data')
    
    if not offer_data:
        st.info("Please generate an offer first")
        return
    
    if not isinstance(offer_data, dict):
        st.error("Invalid offer data")
        return
    
    status = offer_data.get('status')
    if status == 'FINALIZED':
        st.warning("Cannot enhance finalized offers")
        return
    
    # Display current AI content
    ai_content = offer_data.get('ai_content')
    if ai_content:
        st.write("Current AI Content:")
        st.write(ai_content)
        
        fun_fact = offer_data.get('fun_fact')
        if fun_fact:
            st.info(f"Fun Fact: {fun_fact}")
    else:
        st.info("No AI content generated yet")
    
    # Enhancement controls
    if st.button("Generate New AI Content"):
        offer_id = offer_data.get('id')
        if not offer_id:
            st.error("Invalid offer ID")
            return
        
        result = enhance_offer(offer_id)
        if result:
            st.session_state['offer_data'] = result.get('offer')
            st.success("Offer enhanced successfully")
            st.rerun()
        else:
            st.error("Failed to enhance offer")

def render_offer_status():
    """Render status management interface."""
    offer_data = st.session_state.get('offer_data')
    
    if not offer_data:
        st.info("Please generate an offer first")
        return
    
    if not isinstance(offer_data, dict):
        st.error("Invalid offer data")
        return
        
    status = offer_data.get('status')
    if not status:
        st.error("Offer status not available")
        return
        
    st.subheader("Status Management")
    
    # Display current status
    st.write(f"Current Status: **{status}**")
    
    # Status update section
    col1, col2 = st.columns([2, 1])
    with col1:
        status_options = ["DRAFT", "FINALIZED"]
        try:
            current_index = status_options.index(status)
        except ValueError:
            current_index = 0
            
        new_status = st.selectbox(
            "New Status",
            status_options,
            index=current_index
        )
        
        comment = st.text_area("Status Update Comment")
    
    with col2:
        if new_status != status:
            if validate_offer_status_transition(status, new_status):
                offer_id = offer_data.get('id')
                if not offer_id:
                    st.error("Invalid offer ID")
                    return
                    
                if new_status == "FINALIZED":
                    if st.button("Finalize Offer"):
                        result = finalize_offer(offer_id)
                        if result:
                            st.session_state.offer_data = result.get('offer')
                            st.success("Offer finalized successfully")
                            st.rerun()
                        else:
                            st.error("Failed to finalize offer")
                else:
                    if st.button("Update Status"):
                        result = update_offer_status(offer_id, new_status, comment)
                        if result:
                            st.session_state.offer_data = result.get('offer')
                            st.success("Status updated successfully")
                            st.rerun()
                        else:
                            st.error("Failed to update status")
            else:
                st.error("Invalid status transition")
    
    # Display status history
    st.write("---")
    offer_id = offer_data.get('id')
    if offer_id:
        history = get_offer_status_history(offer_id)
        if history:
            display_offer_history(history)
        else:
            st.info("No status history available")
    else:
        st.error("Cannot retrieve status history: Invalid offer ID") 