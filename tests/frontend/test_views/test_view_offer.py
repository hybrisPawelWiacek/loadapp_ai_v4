"""Tests for offer view functionality."""

import pytest
from unittest import mock
from views.view_offer import (
    render_offer_view,
    render_offer_generation,
    render_offer_enhancement,
    render_offer_status
)
from unittest.mock import patch, MagicMock

def test_render_offer_view_no_data(mock_streamlit):
    """Test offer view rendering without required data."""
    render_offer_view()
    assert mock_streamlit['info'].call_count == 2
    mock_streamlit['info'].assert_has_calls([
        mock.call("Please generate an offer first"),
        mock.call("Please generate an offer first")
    ])

def test_render_offer_view_with_data(mock_streamlit):
    """Test offer view rendering with data."""
    mock_data = {
        'route_data': {'id': '123'},
        'cost_data': {'total': '1000.00'}
    }
    
    with patch('streamlit.session_state', mock_data):
        render_offer_view()
        mock_streamlit['title'].assert_called_once()
        mock_streamlit['tabs'].assert_called_once()

def test_render_offer_generation_no_offer(mock_streamlit):
    """Test offer generation rendering without existing offer."""
    with patch('streamlit.session_state', {'route_data': {'id': '123'}}):
        render_offer_generation()
        mock_streamlit['slider'].assert_called_once()
        mock_streamlit['checkbox'].assert_called_once()
        mock_streamlit['button'].assert_called()

def test_render_offer_generation_with_offer(mock_streamlit):
    """Test offer generation rendering with existing offer."""
    mock_offer = {
        'id': '123',
        'final_price': '1150.00',
        'margin_percentage': '15.0',
        'status': 'DRAFT',
        'ai_content': 'Test content'
    }
    
    mock_session_state = {
        'offer_data': mock_offer,
        'route_data': {'id': '123'}
    }
    
    with patch('streamlit.session_state', mock_session_state):
        with patch('views.view_offer.display_offer_details') as mock_display:
            render_offer_generation()
            mock_display.assert_called_once_with(mock_offer)
            mock_streamlit['button'].assert_called_once()

def test_render_offer_enhancement_no_offer(mock_streamlit):
    """Test offer enhancement rendering without offer."""
    with patch('streamlit.session_state', {}):
        render_offer_enhancement()
        mock_streamlit['info'].assert_called_once_with("Please generate an offer first")

def test_render_offer_enhancement_finalized_offer(mock_streamlit):
    """Test offer enhancement rendering with finalized offer."""
    mock_offer = {
        'id': '123',
        'status': 'FINALIZED',
        'ai_content': 'Test content'
    }
    
    with patch('streamlit.session_state', {'offer_data': mock_offer}):
        render_offer_enhancement()
        mock_streamlit['warning'].assert_called_once()

def test_render_offer_status_no_offer(mock_streamlit):
    """Test offer status rendering without offer."""
    render_offer_status()
    mock_streamlit['info'].assert_called_once()

def test_render_offer_status_with_offer(mock_streamlit):
    """Test offer status rendering with offer."""
    mock_offer = {
        'id': '123',
        'status': 'DRAFT',
        'created_at': '2025-01-01T10:00:00Z'
    }
    
    with patch('streamlit.session_state', {'offer_data': mock_offer}):
        render_offer_status()
        mock_streamlit['subheader'].assert_called_once()
        mock_streamlit['selectbox'].assert_called_once() 