"""Tests for the Streamlit frontend application."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import streamlit as st

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent.parent / 'frontend'
if str(frontend_dir) not in sys.path:
    sys.path.append(str(frontend_dir))

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components and functions."""
    with patch('streamlit.title') as mock_title, \
         patch('streamlit.sidebar') as mock_sidebar, \
         patch('streamlit.text') as mock_text, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.success') as mock_success:
        yield {
            'title': mock_title,
            'sidebar': mock_sidebar,
            'text': mock_text,
            'button': mock_button,
            'write': mock_write,
            'success': mock_success
        }

@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Hello, World!"}
        mock_get.return_value = mock_response
        yield mock_get 