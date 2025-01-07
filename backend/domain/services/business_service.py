"""Business service for LoadApp.AI."""
import logging
import structlog
from typing import List, Optional, Set
from uuid import UUID

from backend.domain.entities.business import BusinessEntity

# Configure logger
logger = structlog.get_logger()


class BusinessService:
    """Service for managing business entities."""

    REQUIRED_CERTIFICATIONS = ["ISO9001", "TRANSPORT_LICENSE"]
    ALLOWED_OPERATING_COUNTRIES = ["PL", "DE", "CZ", "SK", "HU"]

    def __init__(self, business_repo):
        """Initialize business service with repository."""
        self._business_repo = business_repo
        
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
        logger.debug("business_service.validate_certifications.start",
                    business_entity_id=str(business_entity_id),
                    cargo_type=cargo_type)
                
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
            logger.info("business_service.validate_certifications.requirements",
                       cargo_type=cargo_type,
                       required_certs=required_certs,
                       validation_message="Mock required certifications (not validated in PoC)")
        
        logger.info("business_service.validate_certifications.success",
                   business_entity_id=str(business_entity_id),
                   cargo_type=cargo_type)
        return True

    def validate_operating_countries(self, business_entity_id: UUID, route_countries: Set[str]) -> bool:
        """Mock validation of business entity operating countries.
        
        Note: This is a PoC implementation that always returns True.
        TODO: Implement real country validation when requirements are available.
        
        Args:
            business_entity_id: ID of the business entity
            route_countries: Set of country codes in the route
            
        Returns:
            bool: Always True for PoC
        """
        logger.debug("business_service.validate_operating_countries.start",
                    business_entity_id=str(business_entity_id),
                    route_countries=list(route_countries))
        
        # Mock operating countries (just for logging purposes)
        MOCK_OPERATING_COUNTRIES = {
            "DE", "PL", "CZ", "SK", "AT", "HU"  # Example Central European countries
        }
        
        # Log what would be checked in production
        non_operating_countries = route_countries - MOCK_OPERATING_COUNTRIES
        if non_operating_countries:
            logger.info("business_service.validate_operating_countries.requirements",
                       non_operating_countries=list(non_operating_countries),
                       validation_message="Countries that would require validation in production (not validated in PoC)")
        
        logger.info("business_service.validate_operating_countries.success",
                   business_entity_id=str(business_entity_id),
                   route_countries=list(route_countries))
        return True

    def validate_business_for_route(self, business_entity_id: UUID, cargo_type: str, route_countries: List[str]) -> bool:
        """
        Validate if business can handle a route.
        For PoC, checks both certifications and operating countries.
        
        Args:
            business_entity_id: ID of the business entity
            cargo_type: Type of cargo being transported
            route_countries: List of country codes in the route
            
        Returns:
            bool: True if business passes all validations
        """
        logger.debug("business_service.validate_business_for_route.start",
                    business_entity_id=str(business_entity_id),
                    cargo_type=cargo_type,
                    route_countries=route_countries)
        
        cert_valid = self.validate_certifications(cargo_type, business_entity_id)
        countries_valid = self.validate_operating_countries(business_entity_id, set(route_countries))
        
        result = cert_valid and countries_valid
        logger.info("business_service.validate_business_for_route.complete",
                   business_entity_id=str(business_entity_id),
                   result=result,
                   validations={
                       "certifications": cert_valid,
                       "operating_countries": countries_valid
                   })
        return result 

    def list_active_businesses(self) -> List[BusinessEntity]:
        """List all active business entities.
        
        Returns:
            List[BusinessEntity]: List of active business entities
            
        Raises:
            RuntimeError: If database session is not initialized
            SQLAlchemyError: If database query fails
        """
        logger.debug("business_service.list_active_businesses.start")
        
        try:
            businesses = self._business_repo.find_all(filters={"is_active": True})
            logger.info("business_service.list_active_businesses.success", count=len(businesses))
            return businesses
            
        except SQLAlchemyError as e:
            if hasattr(self._business_repo.session, 'rollback'):
                self._business_repo.session.rollback()
                logger.info("business_service.list_active_businesses.rollback")
            logger.error("business_service.list_active_businesses.error", error=str(e))
            raise
        except Exception as e:
            logger.error("business_service.list_active_businesses.error", error=str(e))
            raise 