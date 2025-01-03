"""Business service for LoadApp.AI."""
from typing import List, Optional
from uuid import UUID

from backend.domain.entities.business import BusinessEntity


class BusinessService:
    """Service for managing business entities."""

    REQUIRED_CERTIFICATIONS = ["ISO9001", "TRANSPORT_LICENSE"]
    ALLOWED_OPERATING_COUNTRIES = ["PL", "DE", "CZ", "SK", "HU"]

    def validate_certifications(self, cargo_type: str, business_entity_id: UUID) -> bool:
        """Mock validation of business entity certifications for cargo type.
        
        Note: This is a PoC implementation that always returns True.
        TODO: Implement real certification validation when requirements are available.
        
        Args:
            cargo_type: Type of cargo being transported
            business_entity_id: ID of the business entity
            
        Returns:
            bool: Always True for PoC
        """
        logger.info("business_entity.certification.validate",
                    business_entity_id=str(business_entity_id),
                    cargo_type=cargo_type,
                    message="Mock certification validation - always returns True for PoC")
                
        # Mock certification requirements mapping
        MOCK_REQUIRED_CERTS = {
            "hazardous": ["HAZMAT", "ADR"],
            "perishable": ["HACCP", "GDP"],
            "oversized": ["OSCT", "HVCT"],
            "general": []
        }
        
        # Log what would be checked in production
        required_certs = MOCK_REQUIRED_CERTS.get(cargo_type, [])
        if required_certs:
            logger.info("business_entity.certification.requirements",
                       cargo_type=cargo_type,
                       required_certs=required_certs,
                       message="Mock required certifications (not validated in PoC)")
        
        return True

    def validate_operating_countries(self, business_entity_id: UUID, route_countries: set[str]) -> bool:
        """Mock validation of business entity operating countries.
        
        Note: This is a PoC implementation that always returns True.
        TODO: Implement real country validation when requirements are available.
        
        Args:
            business_entity_id: ID of the business entity
            route_countries: Set of country codes in the route
            
        Returns:
            bool: Always True for PoC
        """
        logger.info("business_entity.countries.validate",
                    business_entity_id=str(business_entity_id),
                    route_countries=list(route_countries),
                    message="Mock operating countries validation - always returns True for PoC")
        
        # Mock operating countries (just for logging purposes)
        MOCK_OPERATING_COUNTRIES = {
            "DE", "PL", "CZ", "SK", "AT", "HU"  # Example Central European countries
        }
        
        # Log what would be checked in production
        non_operating_countries = route_countries - MOCK_OPERATING_COUNTRIES
        if non_operating_countries:
            logger.info("business_entity.countries.requirements",
                       non_operating_countries=list(non_operating_countries),
                       message="Countries that would require validation in production (not validated in PoC)")
        
        return True

    def validate_business_for_route(self, business: BusinessEntity, route_countries: List[str]) -> bool:
        """
        Validate if business can handle a route.
        For PoC, checks both certifications and operating countries.
        """
        return (
            self.validate_certifications(business) and 
            self.validate_operating_countries(business, route_countries)
        ) 