import pytest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent / 'backend'
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello_world_endpoint(client):
    response = client.get('/api/hello')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data
