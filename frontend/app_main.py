import streamlit as st

# Must be the first Streamlit command, before any other imports that might use Streamlit
st.set_page_config(
    page_title="LoadApp.AI",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Move other imports after set_page_config
from views import (
    display_input_form,
    render_route_view,
    display_cost_management,
    render_offer_view,
    display_history,
    render_cargo_view
)
from utils.shared_utils import init_cache, cleanup_resources

def main():
    """Main application entry point."""
    # Initialize cache on startup
    init_cache()
    
    # Initialize session state
    if 'cleanup_registered' not in st.session_state:
        st.session_state.cleanup_registered = False
    
    # Check for navigation flag
    if 'should_navigate_to_route' in st.session_state and st.session_state.should_navigate_to_route:
        st.session_state.nav_selection = "Route Planning"
        st.session_state.should_navigate_to_route = False
    
    # Check for offer navigation flag
    if 'should_navigate_to_offer' in st.session_state and st.session_state.should_navigate_to_offer:
        st.session_state.nav_selection = "Offer Generation"
        st.session_state.should_navigate_to_offer = False
    
    # Register cleanup handler
    st.cache_data.clear()
    if not st.session_state.cleanup_registered:
        st.runtime.scriptrunner.add_script_run_ctx(cleanup_resources)
        st.session_state.cleanup_registered = True
    
    # Sidebar navigation
    st.sidebar.title("LoadApp.AI")
    nav_selection = st.sidebar.radio(
        "Navigation",
        ["Transport Input", "Route Planning", "Cost Management", 
         "Offer Generation", "History", "Cargo Management"],
        key="nav_selection"
    )
    
    # Main content based on navigation
    if nav_selection == "Transport Input":
        display_input_form()
    elif nav_selection == "Route Planning":
        render_route_view()
    elif nav_selection == "Cost Management":
        display_cost_management()
    elif nav_selection == "Offer Generation":
        render_offer_view()
    elif nav_selection == "History":
        display_history()
    elif nav_selection == "Cargo Management":
        render_cargo_view()

if __name__ == "__main__":
    main() 