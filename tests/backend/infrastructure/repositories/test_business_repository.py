"""Tests for business repository implementation."""
from decimal import Decimal
from uuid import UUID
import pytest

from backend.domain.entities.business import BusinessEntity
from backend.infrastructure.repositories.business_repository import SQLBusinessEntityRepository


@pytest.fixture
def business_entity():
    """Create a sample business entity for testing."""
    return BusinessEntity(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        name="Test Transport Company",
        address="123 Test St, Test City",
        contact_info={
            "email": "test@business.com",
            "phone": "+1234567890"
        },
        business_type="shipper",
        certifications=["ISO 9001", "SQAS", "HACCP"],
        operating_countries=["DE", "PL", "CZ"],
        cost_overheads={
            "insurance": Decimal("150.50"),
            "permits": Decimal("75.25"),
            "gps": Decimal("25.00"),
            "admin": Decimal("100.00")
        }
    )


class TestSQLBusinessEntityRepository:
    """Test cases for SQLBusinessEntityRepository."""

    def test_save_business_entity(self, db, business_entity):
        """Test saving a business entity."""
        repo = SQLBusinessEntityRepository(db)
        saved_entity = repo.save(business_entity)

        assert saved_entity.id == business_entity.id
        assert saved_entity.name == business_entity.name
        assert saved_entity.address == business_entity.address
        assert saved_entity.contact_info == business_entity.contact_info
        assert saved_entity.business_type == business_entity.business_type
        assert saved_entity.certifications == business_entity.certifications
        assert saved_entity.operating_countries == business_entity.operating_countries
        assert saved_entity.cost_overheads == business_entity.cost_overheads

    def test_find_business_entity_by_id(self, db, business_entity):
        """Test finding a business entity by ID."""
        repo = SQLBusinessEntityRepository(db)
        saved_entity = repo.save(business_entity)
        found_entity = repo.find_by_id(saved_entity.id)

        assert found_entity is not None
        assert found_entity.id == business_entity.id
        assert found_entity.name == business_entity.name
        assert found_entity.address == business_entity.address
        assert found_entity.contact_info == business_entity.contact_info
        assert found_entity.business_type == business_entity.business_type
        assert found_entity.certifications == business_entity.certifications
        assert found_entity.operating_countries == business_entity.operating_countries
        assert found_entity.cost_overheads == business_entity.cost_overheads

    def test_find_nonexistent_business_entity(self, db):
        """Test finding a nonexistent business entity."""
        repo = SQLBusinessEntityRepository(db)
        found_entity = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_entity is None

    def test_save_business_entity_with_minimum_requirements(self, db):
        """Test saving a business entity with minimum required fields."""
        entity = BusinessEntity(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Minimal Transport Company",
            address="456 Min St, Min City",
            contact_info={"email": "min@business.com"},
            business_type="carrier",
            certifications=["ISO 9001"],  # Minimum one certification
            operating_countries=["DE"],    # Minimum one country
            cost_overheads={"insurance": Decimal("100.00")}  # Minimum one overhead
        )
        repo = SQLBusinessEntityRepository(db)
        saved_entity = repo.save(entity)

        assert saved_entity.id == entity.id
        assert saved_entity.name == entity.name
        assert saved_entity.address == entity.address
        assert saved_entity.contact_info == entity.contact_info
        assert saved_entity.business_type == entity.business_type
        assert saved_entity.certifications == entity.certifications
        assert saved_entity.operating_countries == entity.operating_countries
        assert saved_entity.cost_overheads == entity.cost_overheads

    def test_save_business_entity_with_special_characters(self, db):
        """Test saving a business entity with special characters."""
        entity = BusinessEntity(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Spéciål Tränspört GmbH & Co. KG",
            address="789 Spéciål St, Tränspört City",
            contact_info={"email": "special@business.com"},
            business_type="carrier",
            certifications=["ISO 9001", "GDP"],
            operating_countries=["DE", "AT"],
            cost_overheads={"insurance": Decimal("150.50")}
        )
        repo = SQLBusinessEntityRepository(db)
        saved_entity = repo.save(entity)

        assert saved_entity.name == entity.name
        assert saved_entity.address == entity.address
        assert saved_entity.certifications == entity.certifications

    def test_save_business_entity_with_large_overheads(self, db):
        """Test saving a business entity with large decimal values."""
        entity = BusinessEntity(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name="Large Transport Corp",
            address="999 Large St, Big City",
            contact_info={"email": "large@business.com"},
            business_type="carrier",
            certifications=["ISO 9001", "SQAS"],
            operating_countries=["DE", "FR"],
            cost_overheads={
                "insurance": Decimal("9999999.99"),
                "permits": Decimal("8888888.88")
            }
        )
        repo = SQLBusinessEntityRepository(db)
        saved_entity = repo.save(entity)

        assert saved_entity.cost_overheads == entity.cost_overheads 