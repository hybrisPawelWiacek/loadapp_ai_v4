"""Tests for cargo utility functions."""

import pytest
from utils.cargo_utils import (
    create_cargo, get_cargo, list_cargo,
    update_cargo, delete_cargo, get_cargo_status_history,
    display_cargo_details, display_cargo_history
)
from unittest.mock import patch, MagicMock

def test_create_cargo(mock_requests, mock_api_response):
    """Test cargo creation."""
    cargo_data = {
        'weight': 1000,
        'volume': 2.5,
        'cargo_type': 'flatbed',
        'value': '5000.00'
    }
    
    result = create_cargo(cargo_data)
    assert result == mock_api_response
    mock_requests['post'].assert_called_once()

def test_get_cargo(mock_requests, mock_api_response):
    """Test getting cargo details."""
    result = get_cargo('123')
    assert result == mock_api_response
    mock_requests['get'].assert_called_once()

def test_list_cargo(mock_requests, mock_api_response):
    """Test listing cargo entries."""
    result = list_cargo(page=1, size=10)
    assert result == mock_api_response
    mock_requests['get'].assert_called_once()

def test_update_cargo(mock_requests, mock_api_response):
    """Test updating cargo details."""
    update_data = {'status': 'in_transit'}
    result = update_cargo('123', update_data)
    assert result == mock_api_response
    mock_requests['put'].assert_called_once()

def test_delete_cargo(mock_requests):
    """Test deleting cargo."""
    mock_requests['delete'].return_value.status_code = 204
    result = delete_cargo('123')
    assert result is True
    mock_requests['delete'].assert_called_once()

def test_get_cargo_status_history(mock_requests, mock_api_response):
    """Test getting cargo status history."""
    result = get_cargo_status_history('123')
    assert result == mock_api_response
    mock_requests['get'].assert_called_once()

def test_display_cargo_details(mock_streamlit):
    """Test cargo details display."""
    cargo = {
        'weight': 1000,
        'volume': 2.5,
        'value': '5000.00',
        'status': 'pending',
        'cargo_type': 'flatbed',
        'special_requirements': ['fragile']
    }
    
    display_cargo_details(cargo)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['metric'].assert_called()

def test_display_cargo_history(mock_streamlit):
    """Test cargo history display."""
    history = {
        'history': [
            {
                'new_status': 'in_transit',
                'old_status': 'pending',
                'timestamp': '2025-01-01T10:00:00Z',
                'trigger': 'manual',
                'details': {'updated_by': 'user'}
            }
        ]
    }
    
    display_cargo_history(history)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['expander'].assert_called() 