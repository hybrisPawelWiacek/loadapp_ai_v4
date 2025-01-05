"""Tests for offer utility functions."""

import pytest
from utils.offer_utils import (
    generate_offer, get_offer, enhance_offer,
    finalize_offer, update_offer_status, get_offer_status_history,
    display_offer_details, display_offer_history,
    validate_offer_status_transition
)
from unittest.mock import patch, MagicMock

def test_generate_offer(mock_requests, mock_api_response):
    """Test offer generation."""
    result = generate_offer('123', 15.0, True)
    assert result == mock_api_response
    mock_requests['post'].assert_called_once()

def test_get_offer(mock_requests, mock_api_response):
    """Test getting offer details."""
    result = get_offer('123')
    assert result == mock_api_response
    mock_requests['get'].assert_called_once()

def test_enhance_offer(mock_requests, mock_api_response):
    """Test offer enhancement."""
    result = enhance_offer('123')
    assert result == mock_api_response
    mock_requests['post'].assert_called_once()

def test_finalize_offer(mock_requests, mock_api_response):
    """Test offer finalization."""
    result = finalize_offer('123')
    assert result == mock_api_response
    mock_requests['post'].assert_called_once()

def test_update_offer_status(mock_requests, mock_api_response):
    """Test updating offer status."""
    result = update_offer_status('123', 'FINALIZED', 'Test comment')
    assert result == mock_api_response
    mock_requests['put'].assert_called_once()

def test_get_offer_status_history(mock_requests, mock_api_response):
    """Test getting offer status history."""
    result = get_offer_status_history('123')
    assert result == mock_api_response
    mock_requests['get'].assert_called_once()

def test_display_offer_details(mock_streamlit):
    """Test offer details display."""
    offer = {
        'final_price': '1150.00',
        'status': 'DRAFT',
        'margin_percentage': '15.0',
        'created_at': '2025-01-01T10:00:00Z',
        'ai_content': 'Test content',
        'fun_fact': 'Test fact'
    }
    
    with patch('streamlit.columns') as mock_columns:
        # Mock the columns to return objects with metric method
        col1, col2 = MagicMock(), MagicMock()
        mock_columns.return_value = [col1, col2]
        
        display_offer_details(offer)
        
        # Verify metrics were displayed
        col1.metric.assert_called()
        col2.metric.assert_called()
        
        # Verify AI content display
        mock_streamlit['markdown'].assert_called()

def test_display_offer_history(mock_streamlit):
    """Test offer history display."""
    history = [
        {
            'status': 'DRAFT',
            'timestamp': '2025-01-01T10:00:00Z',
            'comment': 'Initial creation'
        },
        {
            'status': 'FINALIZED',
            'timestamp': '2025-01-01T11:00:00Z',
            'comment': 'Approved'
        }
    ]
    
    display_offer_history(history)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['expander'].assert_called()

def test_validate_offer_status_transition():
    """Test offer status transition validation."""
    # Valid transitions
    assert validate_offer_status_transition('DRAFT', 'FINALIZED') is True
    
    # Invalid transitions
    assert validate_offer_status_transition('FINALIZED', 'DRAFT') is False
    assert validate_offer_status_transition('DRAFT', 'INVALID') is False 