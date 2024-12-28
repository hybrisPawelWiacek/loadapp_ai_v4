"""Test the Flask application."""
import pytest
from flask.testing import FlaskClient

from backend.app import create_app
from backend.config import Config


@pytest.fixture
def app(test_config: Config):
    """Create Flask application for testing."""
    app = create_app(test_config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app) -> FlaskClient:
    """Create Flask test client."""
    return app.test_client()


def test_hello_world_endpoint(client: FlaskClient):
    """Test the hello world endpoint."""
    response = client.get('/api/hello')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data


def test_app_configuration(app, test_config: Config):
    """Test that app is configured correctly."""
    assert app.container is not None
    container_config = app.container._config
    
    # Check main configuration sections
    assert container_config['ENV'] == test_config.ENV
    assert container_config['SERVER']['PORT'] == test_config.SERVER.PORT
    assert container_config['DATABASE']['URL'] == test_config.DATABASE.URL
    assert container_config['OPENAI']['API_KEY'] == test_config.OPENAI.API_KEY
    assert container_config['GOOGLE_MAPS']['API_KEY'] == test_config.GOOGLE_MAPS.API_KEY
