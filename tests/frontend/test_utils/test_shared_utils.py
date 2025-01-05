"""Tests for shared utility functions."""

import pytest
from utils.shared_utils import api_request, format_currency, validate_address

def test_api_request_success(mock_requests, mock_api_response):
    """Test successful API request."""
    response = api_request('/test/endpoint', method='GET')
    assert response == mock_api_response
    mock_requests['get'].assert_called_once()

def test_api_request_error(mock_requests):
    """Test API request with error."""
    mock_requests['get'].return_value.status_code = 404
    mock_requests['get'].return_value.json.return_value = {'error': 'Not found'}
    
    response = api_request('/test/endpoint', method='GET')
    assert response is None

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1000) == "€1000.00"
    assert format_currency(1000.5) == "€1000.50"
    assert format_currency(0) == "€0.00"

def test_validate_address():
    """Test address validation."""
    assert validate_address("123 Main St, Berlin, Germany")
    assert not validate_address("")
    assert not validate_address("123 Main St") 