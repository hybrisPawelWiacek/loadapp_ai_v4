"""Tests for input view functionality."""

import pytest
from views.view_input import display_input_form, display_business_entity_selection, display_cargo_details, enhance_transport_selection
from unittest.mock import MagicMock, patch
from datetime import datetime

def test_display_business_entity_selection(mock_streamlit):
    """Test business entity selection display."""
    mock_entities = [
        {
            'id': '123',
            'name': 'Test Company',
            'certifications': ['ISO 9001'],
            'operating_countries': ['DE', 'PL']
        }
    ]
    
    with patch('views.view_input.fetch_business_entities', return_value=mock_entities):
        # Mock selectbox to return the first entity name
        mock_streamlit['selectbox'].return_value = mock_entities[0]['name']
        
        result = display_business_entity_selection()
        
        assert result == mock_entities[0]
        mock_streamlit['selectbox'].assert_called_once()

def test_enhance_transport_selection(mock_streamlit):
    """Test transport type selection with specifications."""
    mock_transport_types = [('123', 'Test Transport')]
    mock_transport_details = {
        'id': '123',
        'name': 'Test Transport',
        'truck_specifications': {
            'fuel_consumption_empty': 0.22,
            'fuel_consumption_loaded': 0.29,
            'toll_class': 'euro6',
            'euro_class': 'EURO6',
            'co2_class': 'A',
            'maintenance_rate_per_km': '0.15'
        },
        'driver_specifications': {
            'daily_rate': '138.0',
            'required_license_type': 'CE',
            'required_certifications': ['ADR']
        }
    }
    
    with patch('views.view_input.fetch_transport_types', return_value=mock_transport_types), \
         patch('views.view_input.api_request', return_value=mock_transport_details):
        # Mock selectbox to return the transport type ID
        mock_streamlit['selectbox'].return_value = mock_transport_types[0][0]
        
        result = enhance_transport_selection()
        
        assert result == mock_transport_types[0][0]
        mock_streamlit['selectbox'].assert_called_once()
        mock_streamlit['expander'].assert_called_once()
        mock_streamlit['metric'].assert_called()

def test_display_cargo_details(mock_streamlit):
    """Test cargo details form display."""
    # Mock input values
    mock_streamlit['number_input'].side_effect = [1000.0, 5000.0]  # weight, value
    mock_streamlit['multiselect'].return_value = ['Fragile']
    
    weight, value, requirements = display_cargo_details()
    
    assert weight == 1000.0
    assert value == 5000.0
    assert requirements == ['Fragile']
    mock_streamlit['number_input'].assert_called()
    mock_streamlit['multiselect'].assert_called_once()

def test_display_input_form(mock_streamlit):
    """Test complete input form display."""
    # Mock form context
    mock_streamlit['form'].return_value.__enter__.return_value = MagicMock()
    mock_streamlit['form'].return_value.__exit__ = MagicMock()
    
    # Mock business entity selection
    mock_entities = [{'id': '123', 'name': 'Test Company'}]
    with patch('views.view_input.fetch_business_entities', return_value=mock_entities):
        mock_streamlit['selectbox'].return_value = mock_entities[0]['name']
        
        # Mock form submission
        mock_streamlit['form'].return_value.form_submit_button.return_value = True
        
        display_input_form()
        
        mock_streamlit['form'].assert_called_once()
        mock_streamlit['selectbox'].assert_called()

def test_display_input_form_validation(mock_streamlit):
    """Test input form validation."""
    # Mock form context
    mock_streamlit['form'].return_value.__enter__.return_value = MagicMock()
    mock_streamlit['form'].return_value.__exit__ = MagicMock()
    
    # Mock invalid inputs
    mock_streamlit['number_input'].return_value = 0  # Invalid weight
    mock_streamlit['text_input'].return_value = ""   # Invalid address
    
    display_input_form()
    
    # Should show validation warnings
    mock_streamlit['warning'].assert_called() 