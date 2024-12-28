"""Transport service for managing transport-related business logic."""
from typing import Optional, Protocol
from uuid import UUID

from ..entities.transport import Transport, TransportType
from ..entities.business import BusinessEntity


class TransportRepository(Protocol):
    """Repository interface for Transport entity."""
    def save(self, transport: Transport) -> Transport:
        """Save a transport instance."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find a transport by ID."""
        ...


class TransportTypeRepository(Protocol):
    """Repository interface for TransportType entity."""
    def find_by_id(self, id: str) -> Optional[TransportType]:
        """Find a transport type by ID."""
        ...

    def list_all(self) -> list[TransportType]:
        """List all available transport types."""
        ...


class TransportService:
    """Service for managing transport-related business logic."""

    def __init__(
        self,
        transport_repo: TransportRepository,
        transport_type_repo: TransportTypeRepository
    ):
        self._transport_repo = transport_repo
        self._transport_type_repo = transport_type_repo

    def create_transport(
        self,
        transport_type_id: str,
        business_entity_id: UUID
    ) -> Optional[Transport]:
        """Create a new transport instance from transport type."""
        # Get transport type configuration
        transport_type = self._transport_type_repo.find_by_id(transport_type_id)
        if not transport_type:
            return None

        # Create new transport instance
        transport = Transport(
            id=UUID(),
            transport_type_id=transport_type.id,
            business_entity_id=business_entity_id,
            truck_specs=transport_type.truck_specifications,
            driver_specs=transport_type.driver_specifications,
            is_active=True
        )

        # Save and return
        return self._transport_repo.save(transport)

    def get_transport(self, transport_id: UUID) -> Optional[Transport]:
        """Retrieve a transport by ID."""
        return self._transport_repo.find_by_id(transport_id)

    def list_transport_types(self) -> list[TransportType]:
        """List all available transport types."""
        return self._transport_type_repo.list_all()

    def validate_transport_for_business(
        self,
        transport: Transport,
        business: BusinessEntity
    ) -> bool:
        """
        Validate if transport is compatible with business entity.
        For PoC, always returns True.
        """
        return True  # Simplified for PoC 