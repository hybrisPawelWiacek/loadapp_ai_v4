"""Tests for main app functionality."""

import pytest
from app_main import main
from unittest.mock import patch, MagicMock

def test_main_app_initialization(mock_streamlit):
    """Test main app initialization."""
    main()
    mock_streamlit['set_page_config'].assert_called_once()
    mock_streamlit['sidebar'].title.assert_called_once()
    assert mock_streamlit['session_state'].cleanup_registered is True

@pytest.mark.parametrize('page_name', [
    'Transport Input',
    'Route Planning',
    'Cost Management',
    'Offer Generation',
    'History',
    'Cargo Management'
])
def test_page_navigation(mock_streamlit, page_name):
    """Test navigation to different pages."""
    # Mock sidebar radio selection
    mock_streamlit['sidebar'].radio.return_value = page_name
    
    # Run main app
    main()
    
    # Verify sidebar was set up
    mock_streamlit['sidebar'].title.assert_called_once()
    mock_streamlit['sidebar'].radio.assert_called_once_with(
        "Navigation",
        ["Transport Input", "Route Planning", "Cost Management", 
         "Offer Generation", "History", "Cargo Management"]
    )
    assert mock_streamlit['session_state'].cleanup_registered is True

def test_app_state_management(mock_streamlit):
    """Test app state management."""
    # Run main app
    main()
    
    # Verify session state initialization
    assert mock_streamlit['session_state'].cleanup_registered is True
    assert isinstance(mock_streamlit['session_state'].route_data, dict)
    assert isinstance(mock_streamlit['session_state'].cargo_data, dict)
    assert isinstance(mock_streamlit['session_state'].offer_data, dict)
    
    # Verify cleanup registration
    mock_streamlit['runtime'].scriptrunner.add_script_run_ctx.assert_called_once() 