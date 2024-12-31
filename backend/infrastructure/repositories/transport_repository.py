"""Repository implementation for transport-related entities."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from ...domain.entities.transport import (
    Transport, TransportType,
    TruckSpecification, DriverSpecification
)
from ..models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from .base import BaseRepository


class SQLTransportRepository(BaseRepository[TransportModel]):
    """SQLAlchemy implementation of TransportRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(TransportModel, db)

    def save(self, transport: Transport) -> Transport:
        """Save a transport instance."""
        # Create specifications if needed
        truck_model = TruckSpecificationModel(
            id=str(uuid4()),
            fuel_consumption_empty=transport.truck_specs.fuel_consumption_empty,
            fuel_consumption_loaded=transport.truck_specs.fuel_consumption_loaded,
            toll_class=transport.truck_specs.toll_class,
            euro_class=transport.truck_specs.euro_class,
            co2_class=transport.truck_specs.co2_class,
            maintenance_rate_per_km=str(transport.truck_specs.maintenance_rate_per_km)  # Convert Decimal to string
        )

        driver_model = DriverSpecificationModel(
            id=str(uuid4()),
            daily_rate=str(transport.driver_specs.daily_rate),  # Convert Decimal to string
            required_license_type=transport.driver_specs.required_license_type,
            required_certifications="[]"  # Will be set by set_certifications
        )
        driver_model.set_certifications(transport.driver_specs.required_certifications)

        # Add specifications to session first
        self._db.add(truck_model)
        self._db.add(driver_model)
        self._db.flush()  # Ensure IDs are generated

        # Create transport model
        model = TransportModel(
            id=str(transport.id),
            transport_type_id=transport.transport_type_id,
            business_entity_id=str(transport.business_entity_id),
            truck_specifications_id=truck_model.id,
            driver_specifications_id=driver_model.id,
            is_active=transport.is_active
        )

        return self._to_domain(self.create(model))

    def find_by_id(self, id: UUID) -> Optional[Transport]:
        """Find a transport by ID."""
        model = self.get(str(id))
        return self._to_domain(model) if model else None

    def find_by_business_entity_id(self, business_entity_id: UUID) -> List[Transport]:
        """Find transports by business entity ID."""
        models = self.list(business_entity_id=str(business_entity_id))
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: TransportModel) -> Transport:
        """Convert model to domain entity."""
        return Transport(
            id=UUID(model.id),
            transport_type_id=model.transport_type_id,
            business_entity_id=UUID(model.business_entity_id),
            truck_specs=TruckSpecification(
                fuel_consumption_empty=model.truck_specifications.fuel_consumption_empty,
                fuel_consumption_loaded=model.truck_specifications.fuel_consumption_loaded,
                toll_class=model.truck_specifications.toll_class,
                euro_class=model.truck_specifications.euro_class,
                co2_class=model.truck_specifications.co2_class,
                maintenance_rate_per_km=Decimal(model.truck_specifications.maintenance_rate_per_km)  # Convert string back to Decimal
            ),
            driver_specs=DriverSpecification(
                daily_rate=Decimal(model.driver_specifications.daily_rate),  # Convert string back to Decimal
                required_license_type=model.driver_specifications.required_license_type,
                required_certifications=model.driver_specifications.get_certifications()
            ),
            is_active=model.is_active
        )


class SQLTransportTypeRepository(BaseRepository[TransportTypeModel]):
    """SQLAlchemy implementation of TransportTypeRepository."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(TransportTypeModel, db)

    def find_by_id(self, id: str) -> Optional[TransportType]:
        """Find a transport type by ID."""
        model = self.get(id)
        return self._to_domain(model) if model else None

    def list_all(self) -> list[TransportType]:
        """List all transport types."""
        return [self._to_domain(model) for model in self.list()]

    def _to_domain(self, model: TransportTypeModel) -> TransportType:
        """Convert model to domain entity."""
        return TransportType(
            id=model.id,
            name=model.name,
            truck_specifications=TruckSpecification(
                fuel_consumption_empty=model.truck_specifications.fuel_consumption_empty,
                fuel_consumption_loaded=model.truck_specifications.fuel_consumption_loaded,
                toll_class=model.truck_specifications.toll_class,
                euro_class=model.truck_specifications.euro_class,
                co2_class=model.truck_specifications.co2_class,
                maintenance_rate_per_km=Decimal(model.truck_specifications.maintenance_rate_per_km)  # Convert string back to Decimal
            ),
            driver_specifications=DriverSpecification(
                daily_rate=Decimal(model.driver_specifications.daily_rate),  # Convert string back to Decimal
                required_license_type=model.driver_specifications.required_license_type,
                required_certifications=model.driver_specifications.get_certifications()
            )
        ) 