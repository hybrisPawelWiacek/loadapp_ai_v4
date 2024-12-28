"""Tests for business domain entities."""
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from backend.domain.entities.business import BusinessEntity


def test_create_valid_business_entity():
    """Test creating a valid business entity."""
    # Arrange
    business_data = {
        "id": uuid4(),
        "name": "Test Transport Company",
        "certifications": ["ISO 9001", "HACCP"],
        "operating_countries": ["DE", "FR", "PL"],
        "cost_overheads": {
            "administration": Decimal("100.50"),
            "insurance": Decimal("250.75"),
            "facilities": Decimal("500.00")
        }
    }

    # Act
    business = BusinessEntity(**business_data)

    # Assert
    assert isinstance(business.id, UUID)
    assert business.name == business_data["name"]
    assert business.certifications == business_data["certifications"]
    assert business.operating_countries == business_data["operating_countries"]
    assert business.cost_overheads == business_data["cost_overheads"]


def test_business_entity_name_validation():
    """Test business entity name validation."""
    # Arrange
    valid_data = {
        "id": uuid4(),
        "certifications": ["ISO 9001"],
        "operating_countries": ["DE"],
        "cost_overheads": {"admin": Decimal("100")}
    }

    # Act & Assert - Empty name
    with pytest.raises(ValidationError, match="name"):
        BusinessEntity(**{**valid_data, "name": ""})

    # Act & Assert - None name
    with pytest.raises(ValidationError, match="name"):
        BusinessEntity(**{**valid_data, "name": None})

    # Act & Assert - Valid name
    business = BusinessEntity(**{**valid_data, "name": "Valid Name"})
    assert business.name == "Valid Name"


def test_business_entity_certifications_validation():
    """Test business entity certifications validation."""
    # Arrange
    valid_data = {
        "id": uuid4(),
        "name": "Test Company",
        "operating_countries": ["DE"],
        "cost_overheads": {"admin": Decimal("100")}
    }

    # Act & Assert - Empty list
    with pytest.raises(ValidationError, match="certifications"):
        BusinessEntity(**{**valid_data, "certifications": []})

    # Act & Assert - None
    with pytest.raises(ValidationError, match="certifications"):
        BusinessEntity(**{**valid_data, "certifications": None})

    # Act & Assert - Valid certifications
    business = BusinessEntity(**{**valid_data, "certifications": ["ISO 9001"]})
    assert business.certifications == ["ISO 9001"]


def test_business_entity_operating_countries_validation():
    """Test business entity operating countries validation."""
    # Arrange
    valid_data = {
        "id": uuid4(),
        "name": "Test Company",
        "certifications": ["ISO 9001"],
        "cost_overheads": {"admin": Decimal("100")}
    }

    # Act & Assert - Empty list
    with pytest.raises(ValidationError, match="operating_countries"):
        BusinessEntity(**{**valid_data, "operating_countries": []})

    # Act & Assert - None
    with pytest.raises(ValidationError, match="operating_countries"):
        BusinessEntity(**{**valid_data, "operating_countries": None})

    # Act & Assert - Valid countries
    business = BusinessEntity(**{**valid_data, "operating_countries": ["DE", "FR"]})
    assert business.operating_countries == ["DE", "FR"]


def test_business_entity_cost_overheads_validation():
    """Test business entity cost overheads validation."""
    # Arrange
    valid_data = {
        "id": uuid4(),
        "name": "Test Company",
        "certifications": ["ISO 9001"],
        "operating_countries": ["DE"]
    }

    # Act & Assert - Empty dict
    business = BusinessEntity(**{**valid_data, "cost_overheads": {}})
    assert business.cost_overheads == {}

    # Act & Assert - None
    with pytest.raises(ValidationError, match="cost_overheads"):
        BusinessEntity(**{**valid_data, "cost_overheads": None})

    # Act & Assert - Invalid decimal values
    with pytest.raises(ValidationError, match="cost_overheads"):
        BusinessEntity(**{**valid_data, "cost_overheads": {"admin": "not a decimal"}})

    # Act & Assert - Valid overheads
    business = BusinessEntity(**{
        **valid_data,
        "cost_overheads": {
            "admin": Decimal("100.50"),
            "insurance": Decimal("250.75")
        }
    })
    assert business.cost_overheads["admin"] == Decimal("100.50")
    assert business.cost_overheads["insurance"] == Decimal("250.75")


def test_business_entity_id_validation():
    """Test business entity ID validation."""
    # Arrange
    valid_data = {
        "name": "Test Company",
        "certifications": ["ISO 9001"],
        "operating_countries": ["DE"],
        "cost_overheads": {"admin": Decimal("100")}
    }

    # Act & Assert - None ID
    with pytest.raises(ValidationError, match="id"):
        BusinessEntity(**{**valid_data, "id": None})

    # Act & Assert - Invalid UUID string
    with pytest.raises(ValidationError, match="id"):
        BusinessEntity(**{**valid_data, "id": "not-a-uuid"})

    # Act & Assert - Valid UUID
    test_uuid = uuid4()
    business = BusinessEntity(**{**valid_data, "id": test_uuid})
    assert business.id == test_uuid


def test_business_entity_model_dump():
    """Test business entity model dump functionality."""
    # Arrange
    test_uuid = uuid4()
    business_data = {
        "id": test_uuid,
        "name": "Test Transport Company",
        "certifications": ["ISO 9001", "HACCP"],
        "operating_countries": ["DE", "FR"],
        "cost_overheads": {
            "admin": Decimal("100.50"),
            "insurance": Decimal("250.75")
        }
    }

    # Act
    business = BusinessEntity(**business_data)
    dumped_data = business.model_dump()

    # Assert
    assert dumped_data["id"] == test_uuid
    assert dumped_data["name"] == business_data["name"]
    assert dumped_data["certifications"] == business_data["certifications"]
    assert dumped_data["operating_countries"] == business_data["operating_countries"]
    assert dumped_data["cost_overheads"] == business_data["cost_overheads"]
``` 