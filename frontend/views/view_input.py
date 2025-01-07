import streamlit as st
from datetime import datetime, timedelta
from utils.shared_utils import (
    fetch_transport_types,
    fetch_business_entities,
    api_request,
    validate_address
)
from views.view_route import render_route_view
import time

def display_business_selection():
    """Display business entity selection form."""
    st.subheader("1. Business Entity")
    
    # Get available business entities
    businesses = api_request("/api/business")
    if not businesses:
        st.warning("No business entities available")
        return None, False
    
    # Create selection options
    business_options = {b["name"]: b for b in businesses}
    
    # Display business selection
    selected_name = st.selectbox(
        "Select Business Entity",
        options=list(business_options.keys()),
        help="Choose the business entity for the route"
    )
    
    if selected_name:
        selected_business = business_options[selected_name]
        
        # Store in session state
        st.session_state['selected_business_entity'] = selected_business
        
        # Display business details
        with st.expander("Business Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Address: {selected_business['address']}")
                st.write(f"Type: {selected_business['business_type']}")
            
            with col2:
                st.write("Operating Countries:")
                for country in selected_business['operating_countries']:
                    st.write(f"• {country}")
                
                st.write("Certifications:")
                for cert in selected_business['certifications']:
                    st.write(f"• {cert}")
        
        return selected_business, True
    
    return None, False

def display_transport_selection():
    """Display transport selection form."""
    st.subheader("3. Transport Selection")
    
    # Get selected business entity from session state
    business_entity = st.session_state.get('selected_business_entity')
    if not business_entity:
        st.warning("Please select a business entity first")
        return None, False
    
    # Get available transports for the business entity
    transports = api_request(f"/api/transport/business/{business_entity['id']}/transports")
    if not transports:
        st.warning("No transports available for the selected business entity")
        return None, False
    
    # Create a list of transport options with their details
    transport_options = {}
    for transport in transports:
        # Get specifications
        truck_specs = transport.get('truck_specs', {})
        driver_specs = transport.get('driver_specs', {})
        
        # Create a descriptive label
        option_label = f"{transport.get('transport_type_id', 'Unknown')} - {truck_specs.get('euro_class', 'N/A')} ({truck_specs.get('toll_class', 'N/A')})"
        transport_options[option_label] = transport
    
    # Display transport selection
    selected_label = st.selectbox(
        "Select Transport",
        options=list(transport_options.keys()),
        help="Choose a transport for this route"
    )
    
    if selected_label:
        selected_transport = transport_options[selected_label]
        
        # Display transport details
        with st.expander("Transport Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("Transport Type:", selected_transport.get('transport_type_id'))
                st.write("Euro Class:", selected_transport.get('truck_specs', {}).get('euro_class'))
                st.write("Toll Class:", selected_transport.get('truck_specs', {}).get('toll_class'))
            
            with col2:
                truck_specs = selected_transport.get('truck_specs', {})
                st.write("Truck Specifications:")
                st.write(f"• Fuel Consumption (Empty): {truck_specs.get('fuel_consumption_empty', 'N/A')} L/km")
                st.write(f"• Fuel Consumption (Loaded): {truck_specs.get('fuel_consumption_loaded', 'N/A')} L/km")
                st.write(f"• CO2 Class: {truck_specs.get('co2_class', 'N/A')}")
                st.write(f"• Maintenance Rate: {truck_specs.get('maintenance_rate_per_km', 'N/A')} EUR/km")
                
                driver_specs = selected_transport.get('driver_specs', {})
                st.write("\nDriver Specifications:")
                st.write(f"• Daily Rate: {driver_specs.get('daily_rate', 'N/A')} EUR/day")
                st.write(f"• Driving Time Rate: {driver_specs.get('driving_time_rate', 'N/A')} EUR/hour")
                st.write(f"• License Type: {driver_specs.get('required_license_type', 'N/A')}")
                st.write(f"• Required Certifications: {', '.join(driver_specs.get('required_certifications', []))}")
                st.write(f"• Overtime Rate Multiplier: {driver_specs.get('overtime_rate_multiplier', '1.5')}x")
                st.write(f"• Max Driving Hours: {driver_specs.get('max_driving_hours', '9')} hours/day")
        
        return selected_transport, True
    
    return None, False

def display_cargo_input():
    """Display cargo input form."""
    st.subheader("2. Cargo Details")
    
    # Cargo type selection
    cargo_type = st.selectbox(
        "Cargo Type",
        ["general", "hazardous", "refrigerated", "oversized"],
        help="Select the type of cargo to be transported"
    )
    
    # Cargo measurements
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cargo_weight = st.number_input(
            "Weight (kg)",
            min_value=0.0,
            value=1000.00,  # Default value
            step=100.0,
            help="Total weight of the cargo in kilograms",
            format="%.2f"
        )
    
    with col2:
        cargo_volume = st.number_input(
            "Volume (m³)",
            min_value=0.0,
            value=10.00,  # Default value
            step=1.0,
            help="Total volume of the cargo in cubic meters",
            format="%.2f"
        )
    
    with col3:
        cargo_value = st.number_input(
            "Value (EUR)",
            min_value=0.0,
            value=1000.00,  # Default value
            step=1000.0,
            help="Declared value of the cargo in EUR",
            format="%.2f"
        )
    
    # Special requirements
    special_requirements = []
    st.write("Special Requirements:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.checkbox("Temperature Controlled", help="Requires specific temperature range"):
            special_requirements.append("temperature_controlled")
        if st.checkbox("Fragile", help="Requires careful handling"):
            special_requirements.append("fragile")
    
    with col2:
        if st.checkbox("High Value", help="Requires additional security"):
            special_requirements.append("high_value")
        if st.checkbox("Express", help="Requires expedited delivery"):
            special_requirements.append("express")
    
    # Validate inputs
    cargo_valid = all([
        cargo_weight > 0,
        cargo_volume > 0,
        cargo_value > 0
    ])
    
    if not cargo_valid:
        st.warning("Please fill in all cargo measurements with values greater than 0")
    
    return cargo_type, cargo_weight, cargo_volume, cargo_value, special_requirements, cargo_valid

def display_route_details():
    """Display route details input form."""
    st.subheader("4. Route Details")
    
    # Location inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        truck_location = st.text_input(
            "Current Truck Location",
            value="magdeburg, germany",  # Default value
            help="Enter the current location of the truck",
            placeholder="e.g., Alexanderplatz 1, 10178 Berlin, Germany"
        )
        if truck_location:
            if validate_address(truck_location):
                st.success("✓ Valid truck location")
            else:
                st.warning("Please enter a complete address")

    with col2:
        origin = st.text_input(
            "Origin Address",
            value="berlin, germany",  # Default value
            help="Enter the full pickup address",
            placeholder="e.g., Hauptstraße 1, 10115 Berlin, Germany"
        )
        if origin:
            if validate_address(origin):
                st.success("✓ Valid origin address")
            else:
                st.warning("Please enter a complete address")
                
    with col3:
        destination = st.text_input(
            "Destination Address",
            value="warsaw, poland",  # Default value
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
    
    return truck_location, origin, destination, pickup_datetime, delivery_datetime, timeline_valid

def display_input_form():
    """Display the main input form."""
    st.title("Route Planning")
    
    # Business entity selection
    business_entity, business_valid = display_business_selection()
    if not business_valid:
        return
    
    # Cargo input
    cargo_type, cargo_weight, cargo_volume, cargo_value, special_requirements, cargo_valid = display_cargo_input()
    if not cargo_valid:
        return
    
    # Transport selection
    transport, transport_valid = display_transport_selection()
    if not transport_valid:
        return
    
    # Route details
    truck_location, origin, destination, pickup_datetime, delivery_datetime, timeline_valid = display_route_details()
    if not all([truck_location, origin, destination, timeline_valid]):
        return
    
    # Calculate button
    if st.button("Calculate Route", type="primary"):
        if not all([business_valid, cargo_valid, transport_valid, timeline_valid]):
            st.error("Please fill in all required fields")
            return
        
        try:
            # Create cargo first
            cargo_data = {
                "cargo_type": cargo_type,
                "weight": cargo_weight,
                "volume": cargo_volume,
                "value": str(cargo_value),
                "special_requirements": special_requirements,
                "business_entity_id": business_entity['id']
            }
            
            with st.spinner("Creating cargo entry..."):
                cargo = api_request("/api/cargo", method="POST", data=cargo_data)
                if not cargo:
                    st.error("Failed to create cargo entry")
                    return
                
                # Get cargo ID
                cargo_id = cargo.get('id')
                if not cargo_id:
                    st.error("Created cargo is missing ID")
                    return
                
                # Multiple attempts to verify cargo with exponential backoff
                max_attempts = 5
                base_delay = 1  # Start with 1 second
                verification = None
                
                for attempt in range(max_attempts):
                    verification = api_request(f"/api/cargo/{cargo_id}")
                    if verification:
                        break
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                
                if not verification:
                    st.error(f"Unable to verify cargo after {max_attempts} attempts. Please try again.")
                    return
            
            # Calculate route
            with st.spinner("Creating locations..."):
                # Create truck location
                truck_location_data = {
                    "address": truck_location,
                    "business_entity_id": business_entity['id']
                }
                truck_location_obj = api_request("/api/location", method="POST", data=truck_location_data)
                if not truck_location_obj:
                    st.error("Failed to create truck location")
                    return

                # Create origin location
                origin_data = {
                    "address": origin,
                    "business_entity_id": business_entity['id']
                }
                origin_location = api_request("/api/location", method="POST", data=origin_data)
                if not origin_location:
                    st.error("Failed to create origin location")
                    return
                
                # Create destination location
                destination_data = {
                    "address": destination,
                    "business_entity_id": business_entity['id']
                }
                destination_location = api_request("/api/location", method="POST", data=destination_data)
                if not destination_location:
                    st.error("Failed to create destination location")
                    return
            
            # Calculate route with location IDs
            route_data = {
                "cargo_id": cargo_id,
                "transport_id": transport["id"],
                "business_entity_id": business_entity['id'],
                "truck_location_id": truck_location_obj["id"],
                "origin_id": origin_location["id"],
                "destination_id": destination_location["id"],
                "pickup_time": pickup_datetime.isoformat(),
                "delivery_time": delivery_datetime.isoformat()
            }
            
            with st.spinner("Calculating route..."):
                response = api_request("/api/route/calculate", method="POST", data=route_data)
                if response and 'route' in response:
                    # Store route data in session state
                    st.session_state.route_data = response['route']
                    st.success("Route calculated successfully!")
                    st.session_state.should_navigate_to_route = True
                    st.rerun()
                else:
                    st.error("Failed to calculate route. Please check if all inputs are valid.")
        except Exception as e:
            st.error(f"Error during route calculation: {str(e)}")
            return 