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
    assert business_service.validate_certifications(valid_business) is True


def test_validate_certifications_with_one_required_cert(business_service: BusinessService, valid_business: BusinessEntity):
    """Test certification validation with only one required certification."""
    valid_business.certifications = ["ISO9001"]
    assert business_service.validate_certifications(valid_business) is True


def test_validate_certifications_with_invalid_certs(business_service: BusinessService, valid_business: BusinessEntity):
    """Test certification validation with invalid certifications."""
    valid_business.certifications = ["INVALID_CERT"]
    assert business_service.validate_certifications(valid_business) is False


def test_validate_operating_countries_with_valid_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with valid route."""
    route_countries = ["PL", "DE"]
    assert business_service.validate_operating_countries(valid_business, route_countries) is True


def test_validate_operating_countries_with_invalid_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with invalid route."""
    route_countries = ["PL", "FR"]  # FR not in operating countries
    assert business_service.validate_operating_countries(valid_business, route_countries) is False


def test_validate_operating_countries_with_empty_route(business_service: BusinessService, valid_business: BusinessEntity):
    """Test operating countries validation with empty route."""
    route_countries = []
    assert business_service.validate_operating_countries(valid_business, route_countries) is True


def test_validate_business_for_route_valid(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with valid business and route."""
    route_countries = ["PL", "DE"]
    assert business_service.validate_business_for_route(valid_business, route_countries) is True


def test_validate_business_for_route_invalid_certs(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with invalid certifications."""
    route_countries = ["PL", "DE"]
    valid_business.certifications = ["INVALID_CERT"]
    assert business_service.validate_business_for_route(valid_business, route_countries) is False


def test_validate_business_for_route_invalid_countries(business_service: BusinessService, valid_business: BusinessEntity):
    """Test full business validation with invalid operating countries."""
    route_countries = ["PL", "FR"]  # FR not in operating countries
    assert business_service.validate_business_for_route(valid_business, route_countries) is False 