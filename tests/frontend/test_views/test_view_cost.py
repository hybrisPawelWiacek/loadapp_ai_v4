"""Tests for cost view functionality."""

import pytest
from views.view_cost import display_cost_metrics, display_driver_costs, display_event_costs
from unittest.mock import patch

def test_display_cost_metrics(mock_streamlit):
    """Test cost metrics display."""
    cost_data = {
        'total_cost': '1000.00',
        'fuel_costs': {'DE': '500.00', 'PL': '300.00'},
        'toll_costs': {'DE': '150.00', 'PL': '50.00'}
    }
    
    display_cost_metrics(cost_data)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['metric'].assert_called()

def test_display_driver_costs(mock_streamlit):
    """Test driver costs display."""
    driver_costs = {
        'base_cost': '200.00',
        'regular_hours_cost': '300.00',
        'overtime_cost': '100.00',
        'total_cost': '600.00'
    }
    
    display_driver_costs(driver_costs)
    mock_streamlit['metric'].assert_called()

def test_display_event_costs(mock_streamlit):
    """Test event costs display."""
    event_costs = {
        'pickup': '50.00',
        'delivery': '50.00',
        'rest': '30.00'
    }
    
    display_event_costs(event_costs)
    mock_streamlit['metric'].assert_called()

def test_display_cost_metrics_no_data(mock_streamlit):
    """Test cost metrics display with no data."""
    display_cost_metrics(None)
    mock_streamlit['error'].assert_called_once() 