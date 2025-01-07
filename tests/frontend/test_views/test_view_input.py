"""Tests for input view functionality."""

import pytest
from views.view_input import display_input_form, display_business_selection, display_cargo_input, display_transport_selection
from unittest.mock import MagicMock, patch
from datetime import datetime

def test_display_business_selection(mock_streamlit):
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
        
        result = display_business_selection()
        
        assert result[0] == mock_entities[0]
        mock_streamlit['selectbox'].assert_called_once()

def test_display_cargo_input(mock_streamlit):
    """Test cargo details form display."""
    # Mock input values
    mock_streamlit['number_input'].side_effect = [1000.0, 5000.0]  # weight, value
    mock_streamlit['multiselect'].return_value = ['Fragile']
    
    weight, value, requirements = display_cargo_input()
    
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