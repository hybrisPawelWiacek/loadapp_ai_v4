"""Tests for location routes."""
import json
from uuid import uuid4

import pytest
from flask import Flask

from backend.api.routes.location_routes import location_bp
from backend.domain.entities.location import Location


@pytest.fixture
def app():
    """Create Flask test app."""
    app = Flask(__name__)
    app.register_blueprint(location_bp)
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_location():
    """Create a sample location."""
    return Location(
        id=uuid4(),
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )


def test_create_location_success(client, sample_location, mocker):
    """Test successful location creation."""
    # Arrange
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                create_location=mocker.Mock(return_value=sample_location)
            )
        )
    )

    # Act
    response = client.post(
        '/api/location',
        json={'address': 'Berlin, Germany'},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['address'] == sample_location.address
    assert data['latitude'] == sample_location.latitude
    assert data['longitude'] == sample_location.longitude


def test_create_location_missing_address(client):
    """Test location creation with missing address."""
    # Act
    response = client.post(
        '/api/location',
        json={},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Address is required'


def test_create_location_geocoding_failure(client, mocker):
    """Test location creation with geocoding failure."""
    # Arrange
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                create_location=mocker.Mock(
                    side_effect=ValueError("Failed to geocode address")
                )
            )
        )
    )

    # Act
    response = client.post(
        '/api/location',
        json={'address': 'Invalid Address'},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Failed to geocode address' in data['error']


def test_get_location_success(client, sample_location, mocker):
    """Test successful location retrieval."""
    # Arrange
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                get_location=mocker.Mock(return_value=sample_location)
            )
        )
    )

    # Act
    response = client.get(f'/api/location/{sample_location.id}')

    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == str(sample_location.id)
    assert data['address'] == sample_location.address
    assert data['latitude'] == sample_location.latitude
    assert data['longitude'] == sample_location.longitude


def test_get_location_not_found(client, mocker):
    """Test location retrieval for non-existent location."""
    # Arrange
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                get_location=mocker.Mock(return_value=None)
            )
        )
    )

    # Act
    response = client.get(f'/api/location/{uuid4()}')

    # Assert
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Location not found'


def test_validate_location_valid(client, sample_location, mocker):
    """Test validation of a valid location."""
    # Arrange
    validation_result = {
        'valid': True,
        'coordinates': {
            'latitude': sample_location.latitude,
            'longitude': sample_location.longitude
        },
        'formatted_address': sample_location.address
    }
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                validate_location=mocker.Mock(return_value=validation_result)
            )
        )
    )

    # Act
    response = client.post(
        '/api/location/validate',
        json={'address': 'Berlin, Germany'},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is True
    assert data['coordinates']['latitude'] == sample_location.latitude
    assert data['coordinates']['longitude'] == sample_location.longitude
    assert data['formatted_address'] == sample_location.address


def test_validate_location_invalid(client, mocker):
    """Test validation of an invalid location."""
    # Arrange
    validation_result = {
        'valid': False,
        'error': 'Invalid address'
    }
    mocker.patch(
        'backend.api.routes.location_routes.get_container',
        return_value=mocker.Mock(
            location_service=lambda: mocker.Mock(
                validate_location=mocker.Mock(return_value=validation_result)
            )
        )
    )

    # Act
    response = client.post(
        '/api/location/validate',
        json={'address': 'Invalid Address'},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['valid'] is False
    assert 'error' in data


def test_validate_location_missing_address(client):
    """Test location validation with missing address."""
    # Act
    response = client.post(
        '/api/location/validate',
        json={},
        content_type='application/json'
    )

    # Assert
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Address is required' 