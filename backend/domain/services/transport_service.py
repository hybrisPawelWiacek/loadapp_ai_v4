"""Transport service for LoadApp.AI."""
from typing import List, Optional, Protocol
from uuid import UUID, uuid4

from backend.domain.entities.business import BusinessEntity
from backend.domain.entities.transport import Transport, TransportType
from backend.domain.services.business_service import BusinessService


class TransportRepository(Protocol):
    """Repository interface for Transport entities."""

    def save(self, transport: Transport) -> Transport:
        """Save a transport entity."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find a transport by ID."""
        ...


class TransportTypeRepository(Protocol):
    """Repository interface for TransportType entities."""

    def find_by_id(self, id: str) -> Optional[TransportType]:
        """Find a transport type by ID."""
        ...

    def list_all(self) -> list[TransportType]:
        """List all transport types."""
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
            return None

        transport = Transport(
            id=uuid4(),
            transport_type_id=transport_type_id,
            business_entity_id=business_entity_id,
            truck_specs=transport_type.truck_specifications,
            driver_specs=transport_type.driver_specifications
        )
        return self._transport_repo.save(transport)

    def get_transport(self, transport_id: UUID) -> Optional[Transport]:
        """Get a transport by ID."""
        return self._transport_repo.find_by_id(transport_id)

    def list_transport_types(self) -> list[TransportType]:
        """List all available transport types."""
        return self._transport_type_repo.list_all()

    def validate_transport_for_business(
        self,
        transport: Transport,
        business: BusinessEntity,
        route_countries: List[str]
    ) -> bool:
        """
        Validate if transport is compatible with business entity.
        For PoC, checks business certifications and operating countries.
        """
        return self._business_service.validate_business_for_route(business, route_countries) 