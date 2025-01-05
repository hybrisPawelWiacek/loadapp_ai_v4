"""Tests for cargo view functionality."""

import pytest
from views.view_cargo import render_cargo_view, render_cargo_list, render_cargo_details
from unittest.mock import patch, MagicMock

def test_render_cargo_view(mock_streamlit):
    """Test cargo view rendering."""
    render_cargo_view()
    mock_streamlit['title'].assert_called_once()
    mock_streamlit['tabs'].assert_called_once()

def test_render_cargo_list(mock_streamlit):
    """Test cargo list rendering."""
    mock_cargo_list = {
        'items': [
            {
                'id': '123',
                'cargo_type': 'flatbed',
                'weight': 1000,
                'volume': 2.5,
                'status': 'pending',
                'value': '5000.00'
            }
        ],
        'total': 1,
        'pages': 1
    }
    
    with patch('views.view_cargo.list_cargo', return_value=mock_cargo_list):
        render_cargo_list()
        mock_streamlit['subheader'].assert_called_once()
        mock_streamlit['expander'].assert_called()

def test_render_cargo_details_no_selection(mock_streamlit):
    """Test cargo details rendering without selection."""
    render_cargo_details()
    mock_streamlit['info'].assert_called_once()

def test_render_cargo_details_with_selection(mock_streamlit):
    """Test cargo details rendering with selection."""
    mock_cargo = {
        'id': '123',
        'cargo_type': 'flatbed',
        'weight': 1000,
        'volume': 2.5,
        'status': 'pending',
        'value': '5000.00',
        'special_requirements': ['fragile']
    }
    
    with patch('streamlit.session_state', {'selected_cargo_id': '123'}), \
         patch('views.view_cargo.get_cargo', return_value=mock_cargo):
        render_cargo_details()
        mock_streamlit['subheader'].assert_called()
        mock_streamlit['metric'].assert_called() 