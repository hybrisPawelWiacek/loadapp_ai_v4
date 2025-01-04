"""Tests for business entity API routes."""
import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from flask import Flask, g

from backend.api.routes.business_routes import business_bp
from backend.infrastructure.models.business_models import BusinessEntityModel


@pytest.fixture
def app(db):
    """Create Flask test app with business routes."""
    app = Flask(__name__)
    app.register_blueprint(business_bp)
    
    # Add database to app context
    @app.before_request
    def before_request():
        from flask import g
        g.db = db
    
    return app


@pytest.fixture
def sample_business_entities(db):
    """Create sample business entities in the database."""
    entities = [
        BusinessEntityModel(
            id=str(uuid4()),
            name="Active Transport Company",
            address="123 Main St",
            contact_info={"email": "active@test.com"},
            business_type="carrier",
            certifications=["ISO9001"],
            operating_countries=["DE", "PL"],
            cost_overheads={"admin": "100.00"},
            is_active=True
        ),
        BusinessEntityModel(
            id=str(uuid4()),
            name="Inactive Transport Company",
            address="456 Side St",
            contact_info={"email": "inactive@test.com"},
            business_type="carrier",
            certifications=["ISO9001"],
            operating_countries=["DE"],
            cost_overheads={"admin": "100.00"},
            is_active=False
        )
    ]
    
    for entity in entities:
        db.add(entity)
    db.commit()
    
    return entities


def test_list_businesses(client, sample_business_entities):
    """Test listing active business entities."""
    # Act
    response = client.get("/api/business")
    data = json.loads(response.data)
    
    # Assert
    assert response.status_code == 200
    assert len(data) == 1  # Only active entities
    assert data[0]["name"] == "Active Transport Company"
    assert data[0]["is_active"] is True


def test_create_business_not_implemented(client):
    """Test creating business entity returns not implemented."""
    # Act
    response = client.post("/api/business", json={
        "name": "Test Company",
        "address": "Test Address",
        "contact_info": {"email": "test@test.com"},
        "business_type": "carrier"
    })
    
    # Assert
    assert response.status_code == 501
    assert b"Not implemented in PoC" in response.data


def test_get_business_not_implemented(client):
    """Test getting single business entity returns not implemented."""
    # Act
    response = client.get(f"/api/business/{uuid4()}")
    
    # Assert
    assert response.status_code == 501
    assert b"Not implemented in PoC" in response.data


def test_update_business_not_implemented(client):
    """Test updating business entity returns not implemented."""
    # Act
    response = client.put(f"/api/business/{uuid4()}", json={
        "name": "Updated Name"
    })
    
    # Assert
    assert response.status_code == 501
    assert b"Not implemented in PoC" in response.data


def test_validate_business_not_implemented(client):
    """Test validating business entity returns not implemented."""
    # Act
    response = client.post(f"/api/business/{uuid4()}/validate")
    
    # Assert
    assert response.status_code == 501
    assert b"Not implemented in PoC" in response.data


def test_list_businesses_db_error(client, db):
    """Test listing businesses handles database errors."""
    # Arrange - Mock get_db to raise RuntimeError
    with patch('backend.api.routes.business_routes.get_db') as mock_get_db:
        mock_get_db.side_effect = RuntimeError("Database session not initialized")
        
        # Act
        response = client.get("/api/business")
        
        # Assert
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Database error" in data["error"] 