"""Tests for route view functionality."""

import pytest
from views.view_route import render_route_view, display_timeline_events, display_route_segments
from unittest.mock import patch, MagicMock

def test_render_route_view_no_data(mock_streamlit):
    """Test route view rendering without data."""
    with patch('streamlit.session_state', {}):
        render_route_view()
        # Multiple info messages are expected for different sections
        assert mock_streamlit['info'].call_count >= 1
        mock_streamlit['info'].assert_any_call("No route data available")

def test_render_route_view_with_data(mock_streamlit):
    """Test route view rendering with data."""
    mock_data = {
        'id': '123',
        'total_distance_km': 500,
        'total_duration_hours': 8,
        'status': 'DRAFT',
        'timeline_events': [],
        'country_segments': []
    }
    
    with patch('streamlit.session_state', {'route_data': mock_data}):
        with patch('views.view_route.render_timeline_management') as mock_timeline:
            with patch('views.view_route.render_route_segments') as mock_segments:
                with patch('views.view_route.render_empty_driving_management') as mock_empty:
                    with patch('views.view_route.render_route_optimization') as mock_opt:
                        with patch('views.view_route.render_status_management') as mock_status:
                            with patch('streamlit.columns') as mock_columns:
                                # Mock the columns to return objects with metric method
                                col1, col2, col3 = MagicMock(), MagicMock(), MagicMock()
                                mock_columns.return_value = [col1, col2, col3]
                                
                                render_route_view()
                                
                                # Verify metrics were displayed
                                col1.metric.assert_called()
                                col2.metric.assert_called()
                                col3.metric.assert_called()
                                
                                # Verify sub-views were called
                                mock_timeline.assert_called_once()
                                mock_segments.assert_called_once()
                                mock_empty.assert_called_once()
                                mock_opt.assert_called_once()
                                mock_status.assert_called_once()

def test_display_timeline_events(mock_streamlit):
    """Test timeline events display."""
    events = [
        {
            'type': 'pickup',
            'location': {
                'address': 'Test Address',
                'latitude': 52.0,
                'longitude': 21.0
            },
            'planned_time': '2025-01-01T10:00:00Z',
            'duration_hours': 1,
            'event_order': 0
        }
    ]
    
    display_timeline_events(events)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['write'].assert_called()

def test_display_route_segments(mock_streamlit):
    """Test route segments display."""
    segments = [
        {
            'country_code': 'DE',
            'distance_km': 100,
            'duration_hours': 2,
            'start_location': {'address': 'Start'},
            'end_location': {'address': 'End'}
        }
    ]
    
    display_route_segments(segments)
    mock_streamlit['subheader'].assert_called_once()
    mock_streamlit['metric'].assert_called() 