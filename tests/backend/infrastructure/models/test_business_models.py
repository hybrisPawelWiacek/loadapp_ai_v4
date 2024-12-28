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
        "certifications": json.dumps(["ISO9001", "HACCP"]),
        "operating_countries": json.dumps(["DE", "PL", "CZ"]),
        "cost_overheads": json.dumps({
            "admin": "100.00",
            "insurance": "250.00",
            "maintenance": "150.00"
        })
    }


def test_business_entity_model_creation(db_session, business_entity_data):
    """Test creating a business entity model."""
    entity = BusinessEntityModel(**business_entity_data)
    db_session.add(entity)
    db_session.commit()

    saved_entity = db_session.query(BusinessEntityModel).filter_by(id=business_entity_data["id"]).first()
    assert saved_entity is not None
    assert saved_entity.name == business_entity_data["name"]
    assert saved_entity.certifications == business_entity_data["certifications"]
    assert saved_entity.operating_countries == business_entity_data["operating_countries"]
    assert saved_entity.cost_overheads == business_entity_data["cost_overheads"]


def test_business_entity_required_fields(db_session):
    """Test that required fields raise IntegrityError when missing."""
    with pytest.raises(IntegrityError):
        entity = BusinessEntityModel(id=str(uuid4()))  # Missing required fields
        db_session.add(entity)
        db_session.commit()


def test_business_entity_json_methods(db_session, business_entity_data):
    """Test JSON getter/setter methods."""
    entity = BusinessEntityModel(**business_entity_data)

    # Test get_certifications
    certifications = entity.get_certifications()
    assert isinstance(certifications, list)
    assert "ISO9001" in certifications
    assert "HACCP" in certifications

    # Test set_certifications
    new_certifications = ["ISO9001", "HACCP", "GDP"]
    entity.set_certifications(new_certifications)
    assert json.loads(entity.certifications) == new_certifications

    # Test get_operating_countries
    countries = entity.get_operating_countries()
    assert isinstance(countries, list)
    assert "DE" in countries
    assert "PL" in countries
    assert "CZ" in countries

    # Test set_operating_countries
    new_countries = ["DE", "PL", "CZ", "AT"]
    entity.set_operating_countries(new_countries)
    assert json.loads(entity.operating_countries) == new_countries

    # Test get_cost_overheads
    overheads = entity.get_cost_overheads()
    assert isinstance(overheads, dict)
    assert overheads["admin"] == "100.00"
    assert overheads["insurance"] == "250.00"
    assert overheads["maintenance"] == "150.00"

    # Test set_cost_overheads
    new_overheads = {
        "admin": "120.00",
        "insurance": "275.00",
        "maintenance": "160.00",
        "it_support": "50.00"
    }
    entity.set_cost_overheads(new_overheads)
    assert json.loads(entity.cost_overheads) == new_overheads


def test_business_entity_empty_json_fields(db_session):
    """Test handling of empty JSON fields."""
    entity = BusinessEntityModel(
        id=str(uuid4()),
        name="Empty Test Company",
        certifications=json.dumps([]),
        operating_countries=json.dumps([]),
        cost_overheads=json.dumps({})
    )
    db_session.add(entity)
    db_session.commit()

    saved_entity = db_session.query(BusinessEntityModel).filter_by(id=entity.id).first()
    assert saved_entity is not None
    assert saved_entity.get_certifications() == []
    assert saved_entity.get_operating_countries() == []
    assert saved_entity.get_cost_overheads() == {} 