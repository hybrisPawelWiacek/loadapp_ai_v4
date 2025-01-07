"""Service for managing transport entities."""
from datetime import datetime
from typing import List, Optional, Protocol
from uuid import UUID, uuid4

from ..entities.transport import Transport, TransportType, TollRateOverride
from ..entities.business import BusinessEntity


class TransportRepository(Protocol):
    """Repository interface for Transport entity."""
    def save(self, transport: Transport) -> Transport:
        """Save a transport."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find a transport by ID."""
        ...

    def find_by_business_entity_id(self, business_id: UUID) -> List[Transport]:
        """Find all transports for a business."""
        ...


class TransportTypeRepository(Protocol):
    """Repository interface for TransportType entity."""
    def find_by_id(self, id: str) -> Optional[TransportType]:
        """Find a transport type by ID."""
        ...

    def list_all(self) -> List[TransportType]:
        """List all transport types."""
        ...


class BusinessService(Protocol):
    """Business service interface."""
    def validate_business_for_route(self, business: BusinessEntity, route_countries: List[str]) -> bool:
        """Validate if business can operate in given countries."""
        ...


class TransportService:
    """Service for managing transport entities."""

    def __init__(
        self,
        transport_repo: TransportRepository,
        transport_type_repo: TransportTypeRepository,
        business_service: BusinessService
    ):
        """Initialize the service."""
        self._transport_repo = transport_repo
        self._transport_type_repo = transport_type_repo
        self._business_service = business_service

    def create_transport(
        self,
        transport_type_id: str,
        business_entity_id: UUID
    ) -> Optional[Transport]:
        """Create a new transport entity."""
        transport_type = self._transport_type_repo.find_by_id(transport_type_id)
        if not transport_type:
            raise ValueError(f"Transport type {transport_type_id} not found")

        transport = Transport(
            id=uuid4(),
            transport_type_id=transport_type_id,
            business_entity_id=business_entity_id,
            truck_specs=transport_type.truck_specifications,
            driver_specs=transport_type.driver_specifications,
            is_active=True
        )
        return self._transport_repo.save(transport)

    def get_transport(self, transport_id: UUID) -> Optional[Transport]:
        """Get a transport by ID."""
        return self._transport_repo.find_by_id(transport_id)

    def get_transport_types(self) -> List[TransportType]:
        """List all available transport types."""
        return self._transport_type_repo.list_all()

    def get_transport_type(self, type_id: str) -> Optional[TransportType]:
        """Get a specific transport type."""
        return self._transport_type_repo.find_by_id(type_id)

    def get_business_transports(self, business_id: UUID) -> List[Transport]:
        """Get all transports for a business entity."""
        return self._transport_repo.find_by_business_entity_id(business_id)

    def validate_transport_for_business(
        self,
        transport: Transport,
        business: BusinessEntity,
        route_countries: List[str]
    ) -> bool:
        """
        Validate if transport is compatible with business entity.
        Checks:
        1. Business certifications match transport requirements
        2. Business can operate in route countries
        3. Transport is active
        """
        if not transport.is_active:
            return False

        # For PoC, we only check business certifications and operating countries
        return self._business_service.validate_business_for_route(business, route_countries)

    def deactivate_transport(self, transport_id: UUID) -> Optional[Transport]:
        """Deactivate a transport."""
        transport = self.get_transport(transport_id)
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")

        transport.is_active = False
        return self._transport_repo.save(transport)

    def reactivate_transport(self, transport_id: UUID) -> Optional[Transport]:
        """Reactivate a transport."""
        transport = self.get_transport(transport_id)
        if not transport:
            raise ValueError(f"Transport {transport_id} not found")

        transport.is_active = True
        return self._transport_repo.save(transport)

    def validate_transport_specifications(
        self,
        transport: Transport,
        cargo_weight: float,
        cargo_volume: float,
        special_requirements: List[str]
    ) -> bool:
        """
        Validate if transport specifications meet cargo requirements.
        For PoC, this always returns True as per requirements.
        """
        return True  # Always true for PoC as specified in requirements 