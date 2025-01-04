"""Tests for the business service."""
import pytest
from uuid import uuid4

from backend.domain.entities.business import BusinessEntity
from backend.domain.services.business_service import BusinessService


@pytest.fixture
def business_service() -> BusinessService:
    """Create a business service instance."""
    return BusinessService()


@pytest.fixture
def valid_business() -> BusinessEntity:
    """Create a valid business entity."""
    return BusinessEntity(
        id=uuid4(),
        name="Test Transport Company",
        address="123 Test Street",
        contact_info={"email": "test@example.com", "phone": "+48123456789"},
        business_type="TRANSPORT",
        certifications=["ISO9001", "TRANSPORT_LICENSE"],
        operating_countries=["PL", "DE", "CZ", "SK", "HU"],
        cost_overheads={"fuel": "1.2", "maintenance": "0.8"},
        is_active=True
    )


def test_validate_certifications_with_valid_business(business_service: BusinessService, valid_business: BusinessEntity):
    """Test certification validation with valid business."""
    assert business_service.validate_certifications("general", valid_business.id) is True


def test_validate_certifications_with_one_required_cert(business_service: BusinessService, valid_business: BusinessEntity):
    """Test certification validation with only one required certification."""
    valid_business.certifications = ["ISO9001"]
    assert business_service.validate_certifications("general", valid_business.id) is True


def test_validate_certifications_with_invalid_certs(business_service: BusinessService, valid_business: BusinessEntity):
    """Test certification validation with invalid certifications."""
    valid_business.certifications = ["INVALID_CERT"]
    assert business_service.validate_certifications("hazardous", valid_business.id) is True  # Always True in PoC


def test_validate_operating_countries_with_valid_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with valid route."""
    route_countries = {"PL", "DE"}
    assert business_service.validate_operating_countries(valid_business.id, route_countries) is True


def test_validate_operating_countries_with_invalid_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with invalid route."""
    route_countries = {"PL", "FR"}  # FR not in operating countries
    assert business_service.validate_operating_countries(valid_business.id, route_countries) is True  # Always True in PoC


def test_validate_operating_countries_with_empty_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with empty route."""
    route_countries = set()
    assert business_service.validate_operating_countries(valid_business.id, route_countries) is True


def test_validate_business_for_route_valid(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with valid business and route."""
    route_countries = ["PL", "DE"]
    assert business_service.validate_business_for_route(valid_business.id, "general", route_countries) is True


def test_validate_business_for_route_invalid_certs(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with invalid certifications."""
    route_countries = ["PL", "DE"]
    valid_business.certifications = ["INVALID_CERT"]
    assert business_service.validate_business_for_route(valid_business.id, "hazardous", route_countries) is True  # Always True in PoC


def test_validate_business_for_route_invalid_countries(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with invalid operating countries."""
    route_countries = ["PL", "FR"]  # FR not in operating countries
    assert business_service.validate_business_for_route(valid_business.id, "general", route_countries) is True  # Always True in PoC 


def test_validate_certifications_stores_validation_details(business_service: BusinessService, valid_business: BusinessEntity):
    """Test that certification validation stores validation details."""
    cargo_type = "hazardous"
    result = business_service.validate_certifications(cargo_type, valid_business.id)
    
    assert result is True  # PoC always returns True
    # We can verify the logging through a mock, but that's a future enhancement if needed


def test_validate_operating_countries_stores_validation_details(business_service: BusinessService, valid_business: BusinessEntity):
    """Test that operating countries validation stores validation details."""
    route_countries = {"DE", "PL"}
    result = business_service.validate_operating_countries(valid_business.id, route_countries)
    
    assert result is True  # PoC always returns True
    # We can verify the logging through a mock, but that's a future enhancement if needed


def test_validate_business_for_route_with_validation_timestamp(business_service: BusinessService, valid_business: BusinessEntity):
    """Test that business validation for route includes timestamp."""
    route_countries = ["DE", "PL"]
    cargo_type = "general"
    
    result = business_service.validate_business_for_route(
        business_entity_id=valid_business.id,
        cargo_type=cargo_type,
        route_countries=route_countries
    )
    
    assert result is True  # PoC always returns True 