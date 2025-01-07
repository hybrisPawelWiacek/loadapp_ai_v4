"""Service layer for cargo-related operations."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..entities.cargo import Cargo
from ...infrastructure.repositories.cargo_repository import SQLCargoRepository
from ...infrastructure.repositories.business_repository import SQLBusinessRepository
from ...infrastructure.models.cargo_models import CargoStatusHistoryModel

# Valid status transitions for cargo
VALID_STATUS_TRANSITIONS = {
    "pending": ["in_transit", "cancelled"],  # in_transit only after offer finalization
    "in_transit": ["delivered", "cancelled"],
    "delivered": [],  # Terminal state
    "cancelled": []   # Terminal state
}

class CargoService:
    """Service for managing cargo operations."""

    def __init__(self, cargo_repository: SQLCargoRepository, business_repository: SQLBusinessRepository, route_service=None):
        """Initialize service with repositories."""
        self.cargo_repository = cargo_repository
        self.business_repository = business_repository
        self.route_service = route_service

    def create_cargo(self, cargo: Cargo) -> Cargo:
        """Create a new cargo entry."""
        # Validate business entity
        if cargo.business_entity_id:
            business_entity = self.business_repository.find_by_id(cargo.business_entity_id)
            if not business_entity:
                raise ValueError("Business entity not found")
            if not business_entity.is_active:
                raise ValueError("Business entity is not active")

        # Set initial status
        cargo.status = "pending"
        cargo.created_at = datetime.now(timezone.utc)
        
        return self.cargo_repository.save(cargo)

    def update_cargo(self, cargo_id: UUID, updates: Dict) -> Cargo:
        """Update cargo details."""
        cargo = self.cargo_repository.find_by_id(cargo_id)
        if not cargo:
            raise ValueError("Cargo not found")

        # Validate status transition if status is being updated
        if "status" in updates:
            self._validate_status_transition(cargo.status, updates["status"])
            old_status = cargo.status
            cargo.status = updates["status"]
            self._handle_status_change(cargo, old_status, updates.get("trigger", "manual"), updates.get("trigger_id"))

        # Update other fields
        if "weight" in updates:
            cargo.weight = float(updates["weight"])
        if "volume" in updates:
            cargo.volume = float(updates["volume"])
        if "value" in updates:
            cargo.value = Decimal(str(updates["value"]))
        if "special_requirements" in updates:
            cargo.special_requirements = updates["special_requirements"]
        if "cargo_type" in updates:
            cargo.cargo_type = updates["cargo_type"]

        cargo.updated_at = datetime.now(timezone.utc)
        return self.cargo_repository.save(cargo)

    def get_cargo(self, cargo_id: UUID) -> Optional[Cargo]:
        """Get cargo by ID."""
        return self.cargo_repository.find_by_id(cargo_id)

    def list_cargo(self, business_entity_id: Optional[UUID] = None, page: int = 1, size: int = 10) -> Dict:
        """List cargo with optional filtering and pagination."""
        # Implementation depends on repository interface
        # For now, return mock pagination
        return {
            "items": [],
            "total": 0,
            "page": page,
            "size": size
        }

    def delete_cargo(self, cargo_id: UUID) -> bool:
        """Soft delete cargo."""
        cargo = self.cargo_repository.find_by_id(cargo_id)
        if not cargo:
            raise ValueError("Cargo not found")
        
        if cargo.status == "in_transit":
            raise ValueError("Cannot delete cargo in transit")

        cargo.is_active = False
        cargo.updated_at = datetime.now(timezone.utc)
        self.cargo_repository.save(cargo)
        return True

    def handle_offer_finalization(self, cargo_id: UUID, offer_id: UUID):
        """Handle cargo status change after offer finalization."""
        cargo = self.cargo_repository.find_by_id(cargo_id)
        if not cargo:
            raise ValueError("Cargo not found")
            
        if cargo.status != "pending":
            raise ValueError("Cargo must be in pending state for offer finalization")
            
        # Update cargo status
        self._handle_status_change(
            cargo=cargo,
            old_status="pending",
            new_status="in_transit",
            trigger="offer_finalization",
            trigger_id=str(offer_id)
        )
        
        # Notify route service if available
        if self.route_service:
            self.route_service.handle_cargo_status_change(
                cargo_id=cargo_id,
                new_status="in_transit"
            )

    def _validate_status_transition(self, current_status: str, new_status: str):
        """Validate if a status transition is allowed."""
        if current_status == new_status:
            return
            
        if current_status not in VALID_STATUS_TRANSITIONS:
            raise ValueError(f"Invalid current status: {current_status}")
            
        if new_status not in VALID_STATUS_TRANSITIONS[current_status]:
            raise ValueError(f"Invalid status transition: {current_status} -> {new_status}")

    def _handle_status_change(self, cargo: Cargo, old_status: str, new_status: str, trigger: str, trigger_id: Optional[str] = None):
        """Handle cargo status change including history tracking and notifications."""
        # Update cargo status
        cargo.status = new_status
        cargo.updated_at = datetime.now(timezone.utc)
        updated_cargo = self.cargo_repository.save(cargo)

        # Create status history entry
        status_history = CargoStatusHistoryModel(
            id=str(uuid4()),
            cargo_id=str(cargo.id),
            old_status=old_status,
            new_status=new_status,
            trigger=trigger,
            trigger_id=trigger_id,
            details={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": trigger,
                "trigger_id": trigger_id
            }
        )
        # Note: Status history is handled by the model's relationship

        # Notify route service if available
        if self.route_service and old_status != new_status:
            self.route_service.handle_cargo_status_change(
                cargo_id=cargo.id,
                new_status=new_status
            )

        return updated_cargo 