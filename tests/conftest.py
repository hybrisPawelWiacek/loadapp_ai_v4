"""Test configuration and fixtures for both backend and frontend tests."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Project Structure Fixtures
@pytest.fixture(scope="session")
def test_dir():
    """Get the tests directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def project_root(test_dir):
    """Get the project root directory path."""
    return test_dir.parent


# Environment Fixtures
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    env_vars = {
        "ENV": "development",
        "DATABASE_URL": "sqlite:///test.db",
        "SQL_ECHO": "true",
        "TRACK_MODIFICATIONS": "true",
        "OPENAI_API_KEY": "test-api-key",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENAI_MAX_RETRIES": "5",
        "BACKEND_PORT": "5001",
        "FRONTEND_PORT": "8501",
        "DEBUG_MODE": "true",
        "LOG_LEVEL": "DEBUG"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def clean_env():
    """Clean environment variables before and after tests."""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


# Streamlit Fixtures
@pytest.fixture
def mock_streamlit_config():
    """Mock Streamlit configuration."""
    with patch('streamlit.config.get_option') as mock_get_option:
        def get_option(key):
            options = {
                'server.port': 8501,
                'server.address': 'localhost',
                'logger.level': 'INFO'
            }
            return options.get(key)
        mock_get_option.side_effect = get_option
        yield mock_get_option


@pytest.fixture
def mock_streamlit_container():
    """Mock Streamlit container."""
    with patch('streamlit.container') as mock_container:
        container = mock_container.return_value
        container.__enter__.return_value = container
        container.__exit__.return_value = None
        yield container


@pytest.fixture
def mock_streamlit_forms():
    """Mock Streamlit forms."""
    with patch('streamlit.form') as mock_form:
        form = mock_form.return_value
        form.__enter__.return_value = form
        form.__exit__.return_value = None
        yield form


@pytest.fixture
def mock_streamlit_charts():
    """Mock Streamlit chart components."""
    with patch('streamlit.line_chart') as mock_line_chart, \
         patch('streamlit.bar_chart') as mock_bar_chart, \
         patch('streamlit.plotly_chart') as mock_plotly_chart:
        yield {
            'line_chart': mock_line_chart,
            'bar_chart': mock_bar_chart,
            'plotly_chart': mock_plotly_chart
        }


@pytest.fixture
def mock_streamlit_inputs():
    """Mock Streamlit input components."""
    with patch('streamlit.text_input') as mock_text_input, \
         patch('streamlit.number_input') as mock_number_input, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.multiselect') as mock_multiselect:
        yield {
            'text_input': mock_text_input,
            'number_input': mock_number_input,
            'selectbox': mock_selectbox,
            'multiselect': mock_multiselect
        } 