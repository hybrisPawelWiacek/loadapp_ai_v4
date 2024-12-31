"""Tests for business-related SQLAlchemy models."""
import json
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from backend.infrastructure.models.business_models import BusinessEntityModel


@pytest.fixture
def business_entity_data():
    """Fixture for business entity test data."""
    return {
        "id": str(uuid4()),
        "name": "Test Transport Company",
        "address": "123 Test Street, Test City, 12345",
        "contact_info": json.dumps({
            "email": "contact@test.com",
            "phone": "+1234567890"
        }),
        "business_type": "TRANSPORT_COMPANY",
        "certifications": json.dumps(["ISO9001", "HACCP"]),
        "operating_countries": json.dumps(["DE", "PL", "CZ"]),
        "cost_overheads": json.dumps({
            "admin": "100.00",
            "insurance": "250.00",
            "maintenance": "150.00"
        })
    }


def test_business_entity_model_creation(db, business_entity_data):
    """Test creating a business entity model."""
    entity = BusinessEntityModel(**business_entity_data)
    db.add(entity)
    db.commit()

    saved_entity = db.query(BusinessEntityModel).filter_by(id=business_entity_data["id"]).first()
    assert saved_entity is not None
    assert saved_entity.name == business_entity_data["name"]
    assert saved_entity.certifications == business_entity_data["certifications"]
    assert saved_entity.operating_countries == business_entity_data["operating_countries"]
    assert saved_entity.cost_overheads == business_entity_data["cost_overheads"]


def test_business_entity_required_fields(db):
    """Test that required fields raise IntegrityError when missing."""
    # Create entity with missing required fields
    entity = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Company",  # Include name
        address=None,  # Missing address
        contact_info=None,  # Missing contact_info
        business_type=None  # Missing business_type
    )
    db.add(entity)
    with pytest.raises(IntegrityError):
        db.commit()


def test_business_entity_json_methods(db, business_entity_data):
    """Test JSON getter/setter methods."""
    entity = BusinessEntityModel(**business_entity_data)
    db.add(entity)
    db.commit()

    # Test get methods
    assert entity.get_certifications() == ["ISO9001", "HACCP"]
    assert entity.get_operating_countries() == ["DE", "PL", "CZ"]
    assert entity.get_cost_overheads() == {
        "admin": "100.00",
        "insurance": "250.00",
        "maintenance": "150.00"
    }

    # Test set methods
    new_certifications = ["ISO9001", "HACCP", "ADR"]
    new_countries = ["DE", "PL", "CZ", "SK"]
    new_overheads = {
        "admin": "150.00",
        "insurance": "300.00",
        "maintenance": "200.00"
    }

    entity.set_certifications(new_certifications)
    entity.set_operating_countries(new_countries)
    entity.set_cost_overheads(new_overheads)

    db.commit()

    # Verify changes
    assert entity.get_certifications() == new_certifications
    assert entity.get_operating_countries() == new_countries
    assert entity.get_cost_overheads() == new_overheads


def test_business_entity_empty_json_fields(db):
    """Test handling of empty JSON fields."""
    entity = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Company",
        address="123 Test Street",
        contact_info=json.dumps({"email": "test@test.com"}),
        business_type="TRANSPORT_COMPANY"
    )
    db.add(entity)
    db.commit()

    assert entity.get_certifications() == []
    assert entity.get_operating_countries() == []
    assert entity.get_cost_overheads() == {} 