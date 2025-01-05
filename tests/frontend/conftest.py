"""Test fixtures for frontend tests."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone

# Add frontend directory to Python path
frontend_dir = Path(__file__).parent.parent.parent / 'frontend'
if str(frontend_dir) not in sys.path:
    sys.path.append(str(frontend_dir))

class MockSessionState(dict):
    """Mock Streamlit's SessionState."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cleanup_registered = False
        self.route_data = {
            'id': 'test_route_id',
            'status': 'PENDING',
            'distance': 100,
            'duration': 120,
            'cost': 500.0,
            'total_distance_km': 150,
            'total_duration_hours': 2.5,
            'segments': [
                {
                    'id': 'segment1',
                    'start_location': 'A',
                    'end_location': 'B',
                    'distance_km': 75,
                    'duration_hours': 1.2
                },
                {
                    'id': 'segment2',
                    'start_location': 'B',
                    'end_location': 'C',
                    'distance_km': 75,
                    'duration_hours': 1.3
                }
            ],
            'events': [
                {
                    'id': 'event1',
                    'type': 'PICKUP',
                    'location': 'A',
                    'timestamp': '2024-01-05T10:00:00Z',
                    'cost': 50.0
                },
                {
                    'id': 'event2',
                    'type': 'DELIVERY',
                    'location': 'C',
                    'timestamp': '2024-01-05T12:30:00Z',
                    'cost': 75.0
                }
            ],
            'timeline_events': [
                {
                    'id': 'event1',
                    'type': 'PICKUP',
                    'location': 'A',
                    'timestamp': '2024-01-05T10:00:00Z',
                    'cost': 50.0
                },
                {
                    'id': 'event2',
                    'type': 'DELIVERY',
                    'location': 'C',
                    'timestamp': '2024-01-05T12:30:00Z',
                    'cost': 75.0
                }
            ],
            'country_segments': [
                {
                    'id': 'country1',
                    'country': 'Poland',
                    'distance_km': 75,
                    'duration_hours': 1.2
                },
                {
                    'id': 'country2',
                    'country': 'Germany',
                    'distance_km': 75,
                    'duration_hours': 1.3
                }
            ]
        }
        self.cargo_data = {
            'id': 'test_cargo_id',
            'status': 'PENDING',
            'weight': 1000,
            'value': 5000.0,
            'requirements': ['REFRIGERATED'],
            'created_at': '2024-01-05T09:00:00Z',
            'updated_at': '2024-01-05T09:30:00Z',
            'description': 'Test cargo',
            'dimensions': {
                'length': 2.0,
                'width': 1.5,
                'height': 1.8
            }
        }
        self.offer_data = {
            'id': 'test_offer_id',
            'status': 'DRAFT',
            'final_price': 1500.0,
            'base_price': 1000.0,
            'adjustments': [
                {
                    'type': 'DISTANCE',
                    'amount': 200.0,
                    'description': 'Long distance fee'
                },
                {
                    'type': 'REQUIREMENTS',
                    'amount': 300.0,
                    'description': 'Refrigeration fee'
                }
            ],
            'created_at': '2024-01-05T10:30:00Z',
            'updated_at': '2024-01-05T11:00:00Z',
            'valid_until': '2024-01-06T10:30:00Z',
            'route_id': 'test_route_id',
            'cargo_id': 'test_cargo_id',
            'ai_content': 'AI-generated content for the offer'
        }
        self.cost_data = {
            'breakdown': {
                'total_cost': 1000.0,
                'driver_costs': 500.0,
                'fuel_costs': 300.0,
                'maintenance_costs': 200.0,
                'event_costs': [
                    {
                        'event_id': 'event1',
                        'cost': 50.0,
                        'type': 'LOADING'
                    },
                    {
                        'event_id': 'event2',
                        'cost': 75.0,
                        'type': 'UNLOADING'
                    }
                ]
            },
            'settings': {
                'driver_base_rate': 25.0,
                'fuel_rate': 1.5,
                'maintenance_rate': 0.5
            }
        }

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        if key in self:
            del self[key]

class MockTab(MagicMock):
    """Mock for Streamlit tab."""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockColumn(MagicMock):
    """Mock for Streamlit column."""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def create_mock_streamlit():
    """Create a mock streamlit module."""
    mock = {
        'form': MagicMock(),
        'write': MagicMock(),
        'markdown': MagicMock(),
        'metric': MagicMock(),
        'error': MagicMock(),
        'warning': MagicMock(),
        'info': MagicMock(),
        'success': MagicMock(),
        'selectbox': MagicMock(),
        'multiselect': MagicMock(),
        'text_input': MagicMock(),
        'number_input': MagicMock(return_value=100.0),  # Default return value for number inputs
        'date_input': MagicMock(),
        'time_input': MagicMock(),
        'button': MagicMock(),
        'spinner': MagicMock(),
        'empty': MagicMock(),
        'columns': MagicMock(),
        'container': MagicMock(),
        'session_state': MockSessionState(),
        'title': MagicMock(),
        'subheader': MagicMock(),
        'radio': MagicMock(),
        'tabs': MagicMock(),
        'expander': MagicMock(),
        'cache_data': MagicMock(),
        'slider': MagicMock(),
        'checkbox': MagicMock(),
        'dataframe': MagicMock(),
        'download_button': MagicMock(),
        'text_area': MagicMock(),
        'sidebar': MagicMock(),
        'runtime': MagicMock(),
        'set_page_config': MagicMock(),
        'rerun': MagicMock(),  # Add rerun to replace experimental_rerun
    }
    
    # Set up sidebar mock
    mock['sidebar'].title = MagicMock()
    mock['sidebar'].radio = MagicMock()
    
    # Set up runtime mock
    mock['runtime'].scriptrunner = MagicMock()
    mock['runtime'].scriptrunner.add_script_run_ctx = MagicMock()
    
    # Set up cache mock
    mock['cache_data'].clear = MagicMock()
    
    # Set up tabs mock to return mock tabs
    def create_tabs(*args):
        return [MockTab() for _ in range(len(args[0]))]
    mock['tabs'].side_effect = create_tabs
    
    # Set up columns mock to return mock columns
    def create_columns(*args):
        num_cols = args[0] if isinstance(args[0], int) else len(args[0])
        return [MockColumn() for _ in range(num_cols)]
    mock['columns'].side_effect = create_columns
    
    # Set up form mock
    mock['form'].return_value.__enter__ = MagicMock()
    mock['form'].return_value.__exit__ = MagicMock()
    mock['form'].return_value.form_submit_button = MagicMock()
    
    return mock

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock streamlit module for testing."""
    mock = create_mock_streamlit()
    patches = []
    
    # Create patches for all streamlit functions
    for name, value in mock.items():
        patches.append(patch(f'streamlit.{name}', value))
    
    # Start all patches
    for p in patches:
        p.start()
    
    yield mock
    
    # Stop all patches
    for p in patches:
        p.stop()

@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return {
        'status': 'success',
        'data': {
            'route': {
                'id': '123',
                'total_distance_km': 100,
                'total_duration_hours': 5,
                'status': 'NEW',
                'timeline_events': [],
                'country_segments': []
            },
            'cargo': {
                'id': '123',
                'weight': 1000,
                'volume': 2.5,
                'status': 'pending'
            },
            'offer': {
                'id': '123',
                'final_price': '1150.00',
                'status': 'DRAFT'
            }
        }
    }

@pytest.fixture
def mock_requests(mock_api_response):
    """Mock requests library."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Configure mock responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response
        
        # Configure delete response
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        mock_delete.return_value = mock_delete_response
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put,
            'delete': mock_delete
        }

@pytest.fixture
def mock_session_state():
    """Mock session state with common data."""
    return {
        'route_data': {
            'id': '123',
            'total_distance_km': 100,
            'total_duration_hours': 5,
            'status': 'NEW',
            'timeline_events': [],
            'country_segments': []
        },
        'cost_data': {
            'total': '1000.00',
            'breakdown': {
                'fuel_costs': {'DE': '500.00'},
                'toll_costs': {'DE': '200.00'},
                'driver_costs': '300.00'
            }
        },
        'offer_data': {
            'id': '123',
            'final_price': '1150.00',
            'status': 'DRAFT',
            'margin_percentage': '15.0'
        }
    } 