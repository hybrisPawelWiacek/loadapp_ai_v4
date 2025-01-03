"""Business service for LoadApp.AI."""
from typing import List, Optional
from uuid import UUID

from backend.domain.entities.business import BusinessEntity


class BusinessService:
    """Service for managing business entities."""

    REQUIRED_CERTIFICATIONS = ["ISO9001", "TRANSPORT_LICENSE"]
    ALLOWED_OPERATING_COUNTRIES = ["PL", "DE", "CZ", "SK", "HU"]

    def validate_certifications(self, business: BusinessEntity) -> bool:
        """
        Validate if business has required certifications.
        For PoC, checks if business has at least one of the required certifications.
        """
        return any(cert in business.certifications for cert in self.REQUIRED_CERTIFICATIONS)

    def validate_operating_countries(self, business: BusinessEntity, route_countries: List[str]) -> bool:
        """
        Validate if business can operate in given countries.
        For PoC, checks if business operates in all countries on the route.
        """
        return all(country in business.operating_countries for country in route_countries)

    def validate_business_for_route(self, business: BusinessEntity, route_countries: List[str]) -> bool:
        """
        Validate if business can handle a route.
        For PoC, checks both certifications and operating countries.
        """
        return (
            self.validate_certifications(business) and 
            self.validate_operating_countries(business, route_countries)
        ) 