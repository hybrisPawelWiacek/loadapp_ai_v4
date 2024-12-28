"""Tests for transport repository implementations."""
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from backend.domain.entities.transport import (
    Transport, TransportType,
    TruckSpecification, DriverSpecification
)
from backend.infrastructure.repositories.transport_repository import (
    SQLTransportRepository,
    SQLTransportTypeRepository
)
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)


@pytest.fixture
def truck_spec() -> TruckSpecification:
    """Create a sample truck specification."""
    return TruckSpecification(
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="4_axle",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km=Decimal("0.15")
    )


@pytest.fixture
def driver_spec() -> DriverSpecification:
    """Create a sample driver specification."""
    return DriverSpecification(
        daily_rate=Decimal("138.00"),
        required_license_type="CE",
        required_certifications=["ADR", "HACCP"]
    )


@pytest.fixture
def transport_type(truck_spec: TruckSpecification, driver_spec: DriverSpecification) -> TransportType:
    """Create a sample transport type."""
    return TransportType(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications=truck_spec,
        driver_specifications=driver_spec
    )


@pytest.fixture
def transport(truck_spec: TruckSpecification, driver_spec: DriverSpecification) -> Transport:
    """Create a sample transport."""
    return Transport(
        id=uuid4(),
        transport_type_id="flatbed",
        business_entity_id=uuid4(),
        truck_specs=truck_spec,
        driver_specs=driver_spec,
        is_active=True
    )


@pytest.fixture
def transport_type_model(transport_type: TransportType) -> TransportTypeModel:
    """Create a sample transport type model."""
    truck_model = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=transport_type.truck_specifications.fuel_consumption_empty,
        fuel_consumption_loaded=transport_type.truck_specifications.fuel_consumption_loaded,
        toll_class=transport_type.truck_specifications.toll_class,
        euro_class=transport_type.truck_specifications.euro_class,
        co2_class=transport_type.truck_specifications.co2_class,
        maintenance_rate_per_km=str(transport_type.truck_specifications.maintenance_rate_per_km)
    )

    driver_model = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate=str(transport_type.driver_specifications.daily_rate),
        required_license_type=transport_type.driver_specifications.required_license_type,
        required_certifications="[]"  # Will be set by set_certifications
    )
    driver_model.set_certifications(transport_type.driver_specifications.required_certifications)

    return TransportTypeModel(
        id=transport_type.id,
        name=transport_type.name,
        truck_specifications=truck_model,
        driver_specifications=driver_model
    )


class TestSQLTransportRepository:
    """Test cases for SQLTransportRepository."""

    def test_save_transport(self, db: Session, transport: Transport):
        """Test saving a transport instance."""
        # Arrange
        repo = SQLTransportRepository(db)

        # Act
        saved_transport = repo.save(transport)

        # Assert
        assert isinstance(saved_transport, Transport)
        assert saved_transport.id == transport.id
        assert saved_transport.transport_type_id == transport.transport_type_id
        assert saved_transport.business_entity_id == transport.business_entity_id
        assert saved_transport.is_active == transport.is_active

        # Check specifications
        assert saved_transport.truck_specs.fuel_consumption_empty == transport.truck_specs.fuel_consumption_empty
        assert saved_transport.truck_specs.fuel_consumption_loaded == transport.truck_specs.fuel_consumption_loaded
        assert saved_transport.truck_specs.toll_class == transport.truck_specs.toll_class
        assert saved_transport.truck_specs.euro_class == transport.truck_specs.euro_class
        assert saved_transport.truck_specs.co2_class == transport.truck_specs.co2_class
        assert saved_transport.truck_specs.maintenance_rate_per_km == transport.truck_specs.maintenance_rate_per_km

        assert saved_transport.driver_specs.daily_rate == transport.driver_specs.daily_rate
        assert saved_transport.driver_specs.required_license_type == transport.driver_specs.required_license_type
        assert saved_transport.driver_specs.required_certifications == transport.driver_specs.required_certifications

    def test_find_transport_by_id(self, db: Session, transport: Transport):
        """Test finding a transport by ID."""
        # Arrange
        repo = SQLTransportRepository(db)
        saved_transport = repo.save(transport)

        # Act
        found_transport = repo.find_by_id(saved_transport.id)

        # Assert
        assert found_transport is not None
        assert found_transport.id == transport.id
        assert found_transport.transport_type_id == transport.transport_type_id
        assert found_transport.business_entity_id == transport.business_entity_id
        assert found_transport.is_active == transport.is_active

    def test_find_nonexistent_transport(self, db: Session):
        """Test finding a transport that doesn't exist."""
        # Arrange
        repo = SQLTransportRepository(db)

        # Act
        found_transport = repo.find_by_id(uuid4())

        # Assert
        assert found_transport is None


class TestSQLTransportTypeRepository:
    """Test cases for SQLTransportTypeRepository."""

    def test_find_transport_type_by_id(self, db: Session, transport_type: TransportType, transport_type_model: TransportTypeModel):
        """Test finding a transport type by ID."""
        # Arrange
        repo = SQLTransportTypeRepository(db)
        db.add(transport_type_model)
        db.commit()

        # Act
        found_type = repo.find_by_id(transport_type.id)

        # Assert
        assert found_type is not None
        assert found_type.id == transport_type.id
        assert found_type.name == transport_type.name
        assert found_type.truck_specifications.fuel_consumption_empty == transport_type.truck_specifications.fuel_consumption_empty
        assert found_type.truck_specifications.fuel_consumption_loaded == transport_type.truck_specifications.fuel_consumption_loaded
        assert found_type.truck_specifications.toll_class == transport_type.truck_specifications.toll_class
        assert found_type.truck_specifications.euro_class == transport_type.truck_specifications.euro_class
        assert found_type.truck_specifications.co2_class == transport_type.truck_specifications.co2_class
        assert found_type.truck_specifications.maintenance_rate_per_km == transport_type.truck_specifications.maintenance_rate_per_km
        assert found_type.driver_specifications.daily_rate == transport_type.driver_specifications.daily_rate
        assert found_type.driver_specifications.required_license_type == transport_type.driver_specifications.required_license_type
        assert found_type.driver_specifications.required_certifications == transport_type.driver_specifications.required_certifications

    def test_list_all_transport_types(self, db: Session, transport_type_model: TransportTypeModel):
        """Test listing all transport types."""
        # Arrange
        repo = SQLTransportTypeRepository(db)
        db.add(transport_type_model)
        db.commit()

        # Act
        types = repo.list_all()

        # Assert
        assert len(types) == 1
        assert types[0].id == transport_type_model.id
        assert types[0].name == transport_type_model.name

    def test_find_nonexistent_transport_type(self, db: Session):
        """Test finding a transport type that doesn't exist."""
        # Arrange
        repo = SQLTransportTypeRepository(db)

        # Act
        found_type = repo.find_by_id("nonexistent")

        # Assert
        assert found_type is None 