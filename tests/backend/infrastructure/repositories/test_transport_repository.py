"""Tests for transport repository implementations."""
from decimal import Decimal
from uuid import UUID, uuid4
import json

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
from backend.infrastructure.models.business_models import BusinessEntityModel


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
def business_entity_model(db) -> BusinessEntityModel:
    """Create a sample business entity model."""
    model = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info=json.dumps({
            "email": "test@example.com",
            "phone": "+49123456789"
        }),
        business_type="TRANSPORT_COMPANY",
        certifications=json.dumps(["ISO9001"]),
        operating_countries=json.dumps(["DE", "PL"]),
        cost_overheads=json.dumps({
            "admin": "100.00",
            "insurance": "150.00"
        })
    )
    db.add(model)
    db.commit()
    return model


@pytest.fixture
def transport_type_model(truck_spec: TruckSpecification, driver_spec: DriverSpecification, db) -> TransportTypeModel:
    """Create a sample transport type model."""
    truck_model = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=truck_spec.fuel_consumption_empty,
        fuel_consumption_loaded=truck_spec.fuel_consumption_loaded,
        toll_class=truck_spec.toll_class,
        euro_class=truck_spec.euro_class,
        co2_class=truck_spec.co2_class,
        maintenance_rate_per_km=str(truck_spec.maintenance_rate_per_km)
    )

    driver_model = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate=str(driver_spec.daily_rate),
        required_license_type=driver_spec.required_license_type,
        required_certifications=json.dumps(driver_spec.required_certifications)
    )

    model = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications=truck_model,
        driver_specifications=driver_model
    )

    db.add(truck_model)
    db.add(driver_model)
    db.add(model)
    db.commit()
    return model


@pytest.fixture
def transport(truck_spec: TruckSpecification, driver_spec: DriverSpecification, business_entity_model: BusinessEntityModel, transport_type_model: TransportTypeModel) -> Transport:
    """Create a sample transport."""
    return Transport(
        id=uuid4(),
        transport_type_id=transport_type_model.id,
        business_entity_id=UUID(business_entity_model.id),
        truck_specs=truck_spec,
        driver_specs=driver_spec,
        is_active=True
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


class TestSQLTransportRepository:
    """Test cases for SQLTransportRepository."""

    def test_save_transport(self, db: Session, transport: Transport, transport_type_model: TransportTypeModel):
        """Test saving a transport instance."""
        # Arrange
        repo = SQLTransportRepository(db)

        # Act
        saved_transport = repo.save(transport)

        # Assert
        assert isinstance(saved_transport, Transport)
        assert saved_transport.id == transport.id
        assert saved_transport.transport_type_id == transport_type_model.id
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

    def test_find_transport_by_id(self, db: Session, transport: Transport, transport_type_model: TransportTypeModel):
        """Test finding a transport by ID."""
        # Arrange
        repo = SQLTransportRepository(db)
        saved_transport = repo.save(transport)

        # Act
        found_transport = repo.find_by_id(saved_transport.id)

        # Assert
        assert found_transport is not None
        assert found_transport.id == transport.id
        assert found_transport.transport_type_id == transport_type_model.id
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

        # Debug: Verify data exists directly in DB
        result = db.query(TransportTypeModel).filter_by(id="flatbed").first()
        print("\nDirect DB query results:")
        print(f"Found in DB: {result is not None}")
        if result:
            print(f"ID: {result.id}")
            print(f"Name: {result.name}")
            print(f"Truck specs ID: {result.truck_specifications_id}")
            print(f"Driver specs ID: {result.driver_specifications_id}")
            print(f"Has truck specs: {result.truck_specifications is not None}")
            print(f"Has driver specs: {result.driver_specifications is not None}")

        # Debug: Check the session state
        print("\nSession state:")
        print(f"Session in transaction: {db.in_transaction()}")
        print(f"Session is active: {db.is_active}")

        # Act
        found_type = repo.find_by_id(transport_type.id)

        # Debug: Check result
        print("\nRepository query results:")
        print(f"Found by repo: {found_type is not None}")
        if found_type:
            print(f"ID: {found_type.id}")
            print(f"Name: {found_type.name}")

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