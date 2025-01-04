"""Tests for transport-related SQLAlchemy models."""
import json
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.infrastructure.models.transport_models import (
    TruckSpecificationModel,
    DriverSpecificationModel,
    TransportTypeModel,
    TransportModel
)


@pytest.fixture
def truck_spec_data():
    """Fixture for truck specification test data."""
    return {
        "id": str(uuid4()),
        "fuel_consumption_empty": 22.5,
        "fuel_consumption_loaded": 29.0,
        "toll_class": "4_axle",
        "euro_class": "EURO_6",
        "co2_class": "A",
        "maintenance_rate_per_km": "0.15"
    }


@pytest.fixture
def driver_spec_data():
    """Fixture for driver specification test data."""
    return {
        "id": str(uuid4()),
        "daily_rate": "138.50",
        "driving_time_rate": "25.00",
        "required_license_type": "CE",
        "required_certifications": json.dumps(["ADR", "HACCP"])
    }


@pytest.fixture
def transport_type_data(truck_spec_data, driver_spec_data):
    """Fixture for transport type test data."""
    return {
        "id": "flatbed",
        "name": "Flatbed Truck",
        "truck_specifications_id": truck_spec_data["id"],
        "driver_specifications_id": driver_spec_data["id"]
    }


@pytest.fixture
def transport_data(transport_type_data):
    """Fixture for transport test data."""
    return {
        "id": str(uuid4()),
        "transport_type_id": transport_type_data["id"],
        "business_entity_id": str(uuid4()),
        "truck_specifications_id": transport_type_data["truck_specifications_id"],
        "driver_specifications_id": transport_type_data["driver_specifications_id"],
        "is_active": True
    }


def test_truck_specification_model_creation(db, truck_spec_data):
    """Test creating a truck specification model."""
    truck_spec = TruckSpecificationModel(**truck_spec_data)
    db.add(truck_spec)
    db.commit()

    saved_spec = db.query(TruckSpecificationModel).filter_by(id=truck_spec_data["id"]).first()
    assert saved_spec is not None
    assert saved_spec.fuel_consumption_empty == truck_spec_data["fuel_consumption_empty"]
    assert saved_spec.fuel_consumption_loaded == truck_spec_data["fuel_consumption_loaded"]
    assert saved_spec.toll_class == truck_spec_data["toll_class"]
    assert saved_spec.euro_class == truck_spec_data["euro_class"]
    assert saved_spec.co2_class == truck_spec_data["co2_class"]
    assert saved_spec.maintenance_rate_per_km == truck_spec_data["maintenance_rate_per_km"]


def test_driver_specification_model_creation(db, driver_spec_data):
    """Test creating a driver specification model."""
    driver_spec = DriverSpecificationModel(**driver_spec_data)
    db.add(driver_spec)
    db.commit()

    saved_spec = db.query(DriverSpecificationModel).filter_by(id=driver_spec_data["id"]).first()
    assert saved_spec is not None
    assert saved_spec.daily_rate == driver_spec_data["daily_rate"]
    assert saved_spec.required_license_type == driver_spec_data["required_license_type"]
    assert saved_spec.required_certifications == driver_spec_data["required_certifications"]


def test_driver_specification_certifications_methods(db, driver_spec_data):
    """Test driver specification certification getter/setter methods."""
    driver_spec = DriverSpecificationModel(**driver_spec_data)
    
    # Test get_certifications
    certifications = driver_spec.get_certifications()
    assert isinstance(certifications, list)
    assert "ADR" in certifications
    assert "HACCP" in certifications

    # Test set_certifications
    new_certifications = ["ADR", "HACCP", "ISO9001"]
    driver_spec.set_certifications(new_certifications)
    assert json.loads(driver_spec.required_certifications) == new_certifications


def test_transport_type_model_creation(db, transport_type_data, truck_spec_data, driver_spec_data):
    """Test creating a transport type model with relationships."""
    # Create related models first
    truck_spec = TruckSpecificationModel(**truck_spec_data)
    driver_spec = DriverSpecificationModel(**driver_spec_data)
    db.add_all([truck_spec, driver_spec])
    db.commit()

    # Create transport type
    transport_type = TransportTypeModel(**transport_type_data)
    db.add(transport_type)
    db.commit()

    saved_type = db.query(TransportTypeModel).filter_by(id=transport_type_data["id"]).first()
    assert saved_type is not None
    assert saved_type.name == transport_type_data["name"]
    assert saved_type.truck_specifications.id == truck_spec_data["id"]
    assert saved_type.driver_specifications.id == driver_spec_data["id"]


def test_transport_model_creation(db, transport_data, transport_type_data, truck_spec_data, driver_spec_data):
    """Test creating a transport model with relationships."""
    # Enable foreign key constraints
    db.execute(text("PRAGMA foreign_keys=ON"))
    
    # Create business entity first
    from backend.infrastructure.models.business_models import BusinessEntityModel
    business_entity = BusinessEntityModel(
        id=transport_data["business_entity_id"],
        name="Test Business",
        address="123 Test St",
        contact_info={"email": "test@example.com", "phone": "123-456-7890"},
        business_type="CARRIER",
        certifications=[],
        operating_countries=[],
        cost_overheads={}
    )
    db.add(business_entity)
    db.commit()

    # Create related models
    truck_spec = TruckSpecificationModel(**truck_spec_data)
    driver_spec = DriverSpecificationModel(**driver_spec_data)
    db.add_all([truck_spec, driver_spec])
    db.commit()

    transport_type = TransportTypeModel(**transport_type_data)
    db.add(transport_type)
    db.commit()

    # Create transport
    transport = TransportModel(**transport_data)
    db.add(transport)
    db.commit()

    saved_transport = db.query(TransportModel).filter_by(id=transport_data["id"]).first()
    assert saved_transport is not None
    assert saved_transport.transport_type_id == transport_data["transport_type_id"]
    assert saved_transport.business_entity_id == transport_data["business_entity_id"]
    assert saved_transport.is_active == transport_data["is_active"]
    assert saved_transport.truck_specifications.id == truck_spec_data["id"]
    assert saved_transport.driver_specifications.id == driver_spec_data["id"]


def test_transport_model_required_fields(db):
    """Test that transport model requires all necessary fields."""
    from sqlalchemy import text
    
    # Enable foreign key constraints
    db.execute(text("PRAGMA foreign_keys=ON"))
    db.commit()
    
    # Create a transport with missing required fields
    transport = TransportModel(
        id=str(uuid4()),
        business_entity_id=str(uuid4()),  # Non-existent FK
        transport_type_id=str(uuid4()),  # Non-existent FK
        truck_specifications_id=str(uuid4()),  # Non-existent FK
        driver_specifications_id=str(uuid4()),  # Non-existent FK
        is_active=True
    )
    db.add(transport)
    
    # The commit should raise an IntegrityError due to missing foreign keys
    with pytest.raises(IntegrityError):
        db.commit()  # Commit to trigger the foreign key check
    
    # Rollback the failed transaction
    db.rollback()


def test_transport_relationships_cascade_delete(db, transport_data, transport_type_data, truck_spec_data, driver_spec_data):
    """Test that deleting a transport doesn't delete related specifications."""
    # Enable foreign key constraints
    db.execute(text("PRAGMA foreign_keys=ON"))
    
    # Create business entity first (since it's referenced by transport)
    from backend.infrastructure.models.business_models import BusinessEntityModel
    business_entity = BusinessEntityModel(
        id=transport_data["business_entity_id"],
        name="Test Business",
        address="123 Test St",
        contact_info={"email": "test@example.com", "phone": "123-456-7890"},
        business_type="CARRIER",
        certifications=[],
        operating_countries=[],
        cost_overheads={}
    )
    db.add(business_entity)
    db.commit()

    # Create all related models
    truck_spec = TruckSpecificationModel(**truck_spec_data)
    driver_spec = DriverSpecificationModel(**driver_spec_data)
    db.add_all([truck_spec, driver_spec])
    db.commit()

    transport_type = TransportTypeModel(**transport_type_data)
    db.add(transport_type)
    db.commit()

    transport = TransportModel(**transport_data)
    db.add(transport)
    db.commit()

    # Delete transport
    db.delete(transport)
    db.commit()

    # Verify specifications still exist
    assert db.query(TruckSpecificationModel).filter_by(id=truck_spec_data["id"]).first() is not None
    assert db.query(DriverSpecificationModel).filter_by(id=driver_spec_data["id"]).first() is not None
    assert db.query(TransportTypeModel).filter_by(id=transport_type_data["id"]).first() is not None
    assert db.query(BusinessEntityModel).filter_by(id=transport_data["business_entity_id"]).first() is not None 