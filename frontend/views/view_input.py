import streamlit as st
from datetime import datetime, timedelta
from utils.shared_utils import (
    fetch_transport_types,
    fetch_business_entities,
    api_request,
    validate_address
)

def display_business_entity_selection():
    """Display business entity selection with detailed information."""
    st.subheader("1. Business Entity")
    
    entities = fetch_business_entities()
    if not entities:
        st.warning("No business entities available")
        return None
    
    # Create selection box with entity names
    entity_names = [e['name'] for e in entities]
    selected_name = st.selectbox(
        "Business Entity",
        entity_names,
        help="Select the business entity for this transport"
    )
    
    # Find selected entity
    selected_entity = next((e for e in entities if e['name'] == selected_name), None)
    if selected_entity:
        # Display entity details in columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Certifications")
            for cert in selected_entity['certifications']:
                st.markdown(f"- {cert}")
        
        with col2:
            st.markdown("#### Operating Countries")
            countries = ", ".join(selected_entity['operating_countries'])
            st.markdown(f"Operating in: {countries}")
        
        # Store in session state
        st.session_state['selected_business'] = selected_entity
        return selected_entity
    return None

def enhance_transport_selection():
    """Enhanced transport type selection with detailed specifications."""
    st.subheader("2. Transport Details")
    
    transport_types = fetch_transport_types()
    if not transport_types:
        st.warning("No transport types available")
        return None
    
    # Create selection with additional details
    selected_id = st.selectbox(
        "Transport Type",
        [t[0] for t in transport_types],
        format_func=lambda x: next((t[1] for t in transport_types if t[0] == x), x),
        help="Select the type of transport vehicle"
    )
    
    # Fetch and display detailed specifications
    try:
        response = api_request(f"/api/transport/types/{selected_id}/specifications")
        if response:
            with st.expander("View Transport Specifications"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Max Weight", f"{response['max_weight_tons']} tons")
                    st.metric("Max Volume", f"{response['max_volume_m3']} m³")
                with col2:
                    st.metric("Length", f"{response['length_m']} m")
                    st.metric("Height", f"{response['height_m']} m")
        return selected_id
    except Exception as e:
        st.error(f"Error fetching transport specifications: {str(e)}")
        return selected_id

def display_cargo_details():
    """Display cargo details input form."""
    st.subheader("3. Cargo Details")
    
    col1, col2 = st.columns(2)
    with col1:
        cargo_weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            help="Enter the cargo weight in kilograms"
        )
        if cargo_weight > 0:
            st.success("✓ Valid weight provided")
        else:
            st.warning("Weight must be greater than 0")
            
        cargo_value = st.number_input(
            "Value (EUR)",
            min_value=0.0,
            help="Enter the cargo value in EUR"
        )
        if cargo_value > 0:
            st.success("✓ Valid value provided")
        else:
            st.warning("Value must be greater than 0")
            
    with col2:
        special_requirements = st.multiselect(
            "Special Requirements",
            ["Temperature Controlled", "Fragile", "Hazardous", "Express Delivery"],
            help="Select any special handling requirements"
        )
        
        # Additional cargo details expander
        with st.expander("Additional Cargo Details"):
            st.checkbox("Requires special handling equipment")
            st.checkbox("Insurance required")
            st.text_area("Special instructions", placeholder="Enter any special instructions...")
    
    return cargo_weight, cargo_value, special_requirements

def display_route_details():
    """Display route details input form."""
    st.subheader("4. Route Details")
    
    # Location inputs
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input(
            "Origin Address",
            help="Enter the full pickup address",
            placeholder="e.g., Hauptstraße 1, 10115 Berlin, Germany"
        )
        if origin:
            if validate_address(origin):
                st.success("✓ Valid origin address")
            else:
                st.warning("Please enter a complete address")
                
    with col2:
        destination = st.text_input(
            "Destination Address",
            help="Enter the full delivery address",
            placeholder="e.g., Krakowskie Przedmieście 1, 00-001 Warsaw, Poland"
        )
        if destination:
            if validate_address(destination):
                st.success("✓ Valid destination address")
            else:
                st.warning("Please enter a complete address")
    
    # Time selection
    st.subheader("5. Timeline")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Pickup Time")
        pickup_date = st.date_input("Pickup Date")
        pickup_time = st.time_input("Pickup Time")
        pickup_datetime = datetime.combine(pickup_date, pickup_time)
        
    with col2:
        st.write("Delivery Time")
        delivery_date = st.date_input(
            "Delivery Date",
            value=pickup_date + timedelta(days=1),
            min_value=pickup_date
        )
        delivery_time = st.time_input("Delivery Time")
        delivery_datetime = datetime.combine(delivery_date, delivery_time)
    
    # Timeline validation
    if delivery_datetime <= pickup_datetime:
        st.error("⚠️ Delivery time must be after pickup time")
        timeline_valid = False
    else:
        st.success("✓ Timeline is valid")
        timeline_valid = True
    
    return origin, destination, pickup_datetime, delivery_datetime, timeline_valid

def display_input_form():
    """Display the complete input form."""
    with st.form("transport_input", clear_on_submit=False):
        # Business entity selection
        business_entity = display_business_entity_selection()
        
        if not business_entity:
            st.warning("Please select a business entity")
            return
        
        # Transport selection
        transport_type = enhance_transport_selection()
        
        if not transport_type:
            st.warning("Please select a transport type")
            return
        
        # Cargo details
        cargo_weight, cargo_value, special_requirements = display_cargo_details()
        
        if cargo_weight <= 0:
            st.warning("Please enter a valid cargo weight")
        if cargo_value <= 0:
            st.warning("Please enter a valid cargo value")
        
        # Route details
        origin, destination, pickup_datetime, delivery_datetime, timeline_valid = display_route_details()
        
        if not origin:
            st.warning("Please enter an origin address")
        if not destination:
            st.warning("Please enter a destination address")
        if not timeline_valid:
            st.warning("Please ensure delivery time is after pickup time")
        
        # Submit button with validation
        submit_disabled = not all([
            origin,
            destination,
            cargo_weight > 0,
            cargo_value > 0,
            timeline_valid
        ])
        
        submit = st.form_submit_button(
            "Calculate Route",
            disabled=submit_disabled,
            help="All required fields must be filled correctly"
        )
        
        if submit:
            # Create cargo first
            cargo_data = {
                "weight": cargo_weight,
                "value": str(cargo_value),
                "special_requirements": special_requirements,
                "business_entity_id": business_entity['id']
            }
            
            with st.spinner("Creating cargo entry..."):
                cargo = api_request("/api/cargo", method="POST", data=cargo_data)
                if not cargo:
                    st.warning("Failed to create cargo entry")
                    return
            
            # Calculate route
            route_data = {
                "cargo_id": cargo["id"],
                "transport_type_id": transport_type,
                "origin_address": origin,
                "destination_address": destination,
                "pickup_time": pickup_datetime.isoformat(),
                "delivery_time": delivery_datetime.isoformat()
            }
            
            with st.spinner("Calculating route..."):
                route = api_request("/api/route/calculate", method="POST", data=route_data)
                if route:
                    # Store route in session state
                    st.session_state['route_data'] = route
                    # Update workflow step
                    st.session_state['current_step'] = 'route'
                    # Force rerun to update UI
                    st.rerun()
                else:
                    st.warning("Failed to calculate route") 