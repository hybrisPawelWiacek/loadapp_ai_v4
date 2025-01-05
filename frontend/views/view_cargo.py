import streamlit as st
from typing import Dict, Optional
from utils.cargo_utils import (
    create_cargo, list_cargo, get_cargo,
    update_cargo, delete_cargo, get_cargo_status_history,
    display_cargo_details, display_cargo_history
)
from utils.shared_utils import fetch_business_entities

def render_cargo_view():
    """Render the cargo management view."""
    st.title("Cargo Management")
    
    # Tabs for different cargo operations
    tab_list, tab_create, tab_details = st.tabs(["List Cargo", "Create Cargo", "Cargo Details"])
    
    with tab_list:
        render_cargo_list()
    
    with tab_create:
        render_cargo_create_form()
    
    with tab_details:
        render_cargo_details()

def render_cargo_list():
    """Render the cargo listing with pagination."""
    st.subheader("Cargo List")
    
    # Pagination controls
    col1, col2 = st.columns([3, 1])
    with col1:
        page = st.number_input("Page", min_value=1, value=1)
        size = st.selectbox("Items per page", [10, 20, 50], index=0)
    
    with col2:
        business_entities = fetch_business_entities()
        if business_entities:
            business_entity = st.selectbox(
                "Filter by Business",
                options=[("", "All")] + [(be["id"], be["name"]) for be in business_entities],
                format_func=lambda x: x[1]
            )
            business_entity_id = business_entity[0] if business_entity else None
        else:
            business_entity_id = None
    
    # Fetch and display cargo list
    cargo_list = list_cargo(page, size, business_entity_id)
    if cargo_list and cargo_list.get('items'):
        for cargo in cargo_list['items']:
            with st.expander(f"Cargo {cargo['id']} - {cargo['cargo_type']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"Weight: {cargo['weight']} kg")
                    st.write(f"Volume: {cargo['volume']} m³")
                with col2:
                    st.write(f"Status: {cargo['status']}")
                    st.write(f"Value: {cargo['value']}")
                with col3:
                    if st.button("View Details", key=f"view_{cargo['id']}"):
                        st.session_state.selected_cargo_id = cargo['id']
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_{cargo['id']}"):
                        if delete_cargo(cargo['id']):
                            st.success("Cargo deleted successfully")
                            st.rerun()
                        else:
                            st.error("Failed to delete cargo")
        
        # Pagination info
        st.write(f"Page {page} of {cargo_list['pages']} (Total items: {cargo_list['total']})")
    else:
        st.info("No cargo items found")

def render_cargo_create_form():
    """Render the cargo creation form."""
    st.subheader("Create New Cargo")
    
    business_entities = fetch_business_entities()
    if not business_entities:
        st.error("No business entities available")
        return
    
    with st.form("cargo_create_form"):
        business_entity = st.selectbox(
            "Business Entity",
            options=[(be["id"], be["name"]) for be in business_entities],
            format_func=lambda x: x[1]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Weight (kg)", min_value=0.1, step=0.1)
            value = st.number_input("Value (EUR)", min_value=0.0, step=100.0)
        
        with col2:
            volume = st.number_input("Volume (m³)", min_value=0.1, step=0.1)
            cargo_type = st.selectbox("Cargo Type", ["flatbed", "container", "livestock", "refrigerated"])
        
        special_requirements = st.multiselect(
            "Special Requirements",
            ["fragile", "hazardous", "temperature_controlled", "oversized", "insured"]
        )
        
        if st.form_submit_button("Create Cargo"):
            cargo_data = {
                "business_entity_id": business_entity[0],
                "weight": weight,
                "volume": volume,
                "cargo_type": cargo_type,
                "value": str(value),
                "special_requirements": special_requirements
            }
            
            result = create_cargo(cargo_data)
            if result:
                st.success("Cargo created successfully")
                st.session_state.selected_cargo_id = result["id"]
                st.rerun()
            else:
                st.error("Failed to create cargo")

def render_cargo_details():
    """Render detailed cargo information and status history."""
    selected_cargo_id = st.session_state.get('selected_cargo_id')
    
    if not selected_cargo_id:
        st.info("Select a cargo item to view details")
        return
    
    cargo = get_cargo(selected_cargo_id)
    if not cargo:
        st.error("Failed to load cargo details")
        return
    
    # Display cargo details
    st.subheader("Cargo Details")
    display_cargo_details(cargo)
    
    # Status update section
    st.subheader("Update Status")
    current_status = cargo.get('status', 'pending')
    status_options = ["pending", "in_transit", "delivered", "cancelled"]
    try:
        current_index = status_options.index(current_status)
    except ValueError:
        current_index = 0
        
    new_status = st.selectbox(
        "New Status",
        status_options,
        index=current_index
    )
    
    if new_status != current_status:
        if st.button("Update Status"):
            result = update_cargo(selected_cargo_id, {"status": new_status})
            if result:
                st.success("Status updated successfully")
                st.rerun()
            else:
                st.error("Failed to update status")
    
    # Display status history
    st.subheader("Status History")
    history = get_cargo_status_history(selected_cargo_id)
    if history:
        display_cargo_history(history)
    else:
        st.info("No status history available") 