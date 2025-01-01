"""Test configuration and shared fixtures."""
import os
import sys
import pytest
import uuid
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from flask import g
from dataclasses import dataclass
import json
from datetime import datetime, timezone

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.infrastructure.database import Base
from backend.infrastructure.container import Container
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.cargo_models import CargoModel, CostBreakdownModel, CostSettingsModel
from backend.infrastructure.models.route_models import (
    LocationModel,
    EmptyDrivingModel,
    TimelineEventModel,
    CountrySegmentModel,
    RouteModel
)
from backend.infrastructure.models.transport_models import (
    TransportModel,
    TransportTypeModel,
    TruckSpecificationModel,
    DriverSpecificationModel
)
from backend.app import create_app
from backend.config import Config, ServerConfig, DatabaseConfig, OpenAIConfig, GoogleMapsConfig, LoggingConfig, FrontendConfig

# Test database URL - use in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    return Config(
        ENV='testing',
        SERVER=ServerConfig(
            HOST='localhost',
            PORT=5001,
            DEBUG=True
        ),
        DATABASE=DatabaseConfig(
            URL='sqlite:///:memory:',
            ECHO=False,
            TRACK_MODIFICATIONS=False
        ),
        OPENAI=OpenAIConfig(
            API_KEY='test_openai_key',
            MODEL='gpt-4-turbo-preview',
            MAX_RETRIES=1,
            RETRY_DELAY=0.1,
            TIMEOUT=1.0
        ),
        GOOGLE_MAPS=GoogleMapsConfig(
            API_KEY='test_google_maps_key',
            MAX_RETRIES=1,
            RETRY_DELAY=0.1,
            TIMEOUT=1.0,
            CACHE_TTL=60
        ),
        LOGGING=LoggingConfig(
            LEVEL='DEBUG'
        ),
        FRONTEND=FrontendConfig(
            PORT=8501
        )
    )

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db(engine):
    """Create a new database session for a test."""
    connection = engine.connect()
    # Enable foreign key constraints for SQLite
    connection.execute(text("PRAGMA foreign_keys=ON"))
    connection.commit()
    
    transaction = connection.begin()
    session = Session(bind=connection)

    # Start a nested transaction (using SAVEPOINT)
    nested = connection.begin_nested()

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @event.listens_for(session, 'after_transaction_end')
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    # Ensure the session is removed from the registry when it ends
    @event.listens_for(session, 'after_begin')
    def do_begin(session, transaction, connection):
        session.info['nested'] = nested

    @event.listens_for(session, 'after_soft_rollback')
    def do_soft_rollback(session, previous_transaction):
        if session.info.get('nested') is not None:
            session.info['nested'].rollback()
            session.info['nested'] = connection.begin_nested()

    yield session

    # Rollback the overall transaction, restoring the state before the test ran
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def container(test_config, db):
    """Create a test container with test database session."""
    return Container(test_config.to_dict(), db)

@pytest.fixture
def app(test_config, db):
    """Create Flask test app with test database session."""
    app = create_app(test_config)
    
    # Create container with test configuration
    container = Container(test_config.to_dict(), db)
    app.container = container
    
    # Override the database session for testing
    @app.before_request
    def before_request():
        g.db = db
        g.container = container
        # Ensure the session is active and bound
        if not db.is_active:
            db.begin()
        # Ensure all objects are attached to the session
        db.expire_all()
    
    @app.teardown_appcontext
    def teardown_db(exception=None):
        db = g.pop('db', None)
        if db is not None:
            try:
                if exception:
                    db.rollback()
                else:
                    db.commit()
            except:
                db.rollback()
                raise
            finally:
                db.expire_all()
        # Clear container reference
        if hasattr(g, 'container'):
            delattr(g, 'container')
    
    return app

@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()

@pytest.fixture
def business_entity(db):
    """Create a test business entity."""
    entity = BusinessEntityModel(
        id=str(uuid.uuid4()),
        name="Test Business",
        address="123 Test St, Test City",
        contact_info={
            "email": "test@business.com",
            "phone": "+1234567890"
        },
        business_type="shipper",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": "100.00"}
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity 

@pytest.fixture
def test_data(db):
    """Create a complete set of test data with all required entities."""
    # Create business entity
    business_entity = BusinessEntityModel(
        id=str(uuid.uuid4()),
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
    db.refresh(business_entity)
    
    # Create locations
    origin = LocationModel(
        id=str(uuid.uuid4()),
        latitude="52.520008",
        longitude="13.404954",
        address="Berlin, Germany"
    )
    destination = LocationModel(
        id=str(uuid.uuid4()),
        latitude="52.229676",
        longitude="21.012229",
        address="Warsaw, Poland"
    )
    db.add_all([origin, destination])
    db.commit()
    db.refresh(origin)
    db.refresh(destination)
    
    # Create truck and driver specifications
    truck_spec = TruckSpecificationModel(
        id=str(uuid.uuid4()),
        fuel_consumption_empty=22.5,
        fuel_consumption_loaded=29.0,
        toll_class="4_axle",
        euro_class="EURO_6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    driver_spec = DriverSpecificationModel(
        id=str(uuid.uuid4()),
        daily_rate="138.50",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR", "HACCP"])
    )
    db.add_all([truck_spec, driver_spec])
    db.commit()
    db.refresh(truck_spec)
    db.refresh(driver_spec)
    
    # Create transport type
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db.add(transport_type)
    db.commit()
    db.refresh(transport_type)
    
    # Create transport
    transport = TransportModel(
        id=str(uuid.uuid4()),
        transport_type_id=transport_type.id,
        business_entity_id=business_entity.id,
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id,
        is_active=True
    )
    db.add(transport)
    db.commit()
    db.refresh(transport)
    
    # Create cargo
    cargo = CargoModel(
        id=str(uuid.uuid4()),
        business_entity_id=business_entity.id,
        weight=1000.0,
        volume=2.5,
        cargo_type="GENERAL",
        value="5000.00",
        special_requirements=["TAIL_LIFT"],
        status="pending"
    )
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    
    # Create empty driving
    empty_driving = EmptyDrivingModel(
        id=str(uuid.uuid4()),
        distance_km=200.0,
        duration_hours=4.0
    )
    db.add(empty_driving)
    db.commit()
    db.refresh(empty_driving)
    
    # Create route
    route = RouteModel(
        id=str(uuid.uuid4()),
        transport_id=transport.id,
        business_entity_id=business_entity.id,
        cargo_id=cargo.id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc).replace(hour=(datetime.now().hour + 8) % 24),
        empty_driving_id=empty_driving.id,
        total_distance_km=550.5,
        total_duration_hours=8.5,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    
    # Create cost breakdown
    cost_breakdown = CostBreakdownModel(
        id=str(uuid.uuid4()),
        route_id=route.id,
        fuel_costs=json.dumps({"DE": "250.00", "PL": "180.00"}),
        toll_costs=json.dumps({"DE": "120.00", "PL": "85.00"}),
        driver_costs="450.00",
        overhead_costs="175.00",
        timeline_event_costs=json.dumps({
            "loading": "50.00",
            "unloading": "50.00",
            "rest_stop": "25.00"
        }),
        total_cost="1385.00"
    )
    db.add(cost_breakdown)
    db.commit()
    db.refresh(cost_breakdown)
    
    return {
        "business_entity": business_entity,
        "origin": origin,
        "destination": destination,
        "truck_spec": truck_spec,
        "driver_spec": driver_spec,
        "transport_type": transport_type,
        "transport": transport,
        "cargo": cargo,
        "empty_driving": empty_driving,
        "route": route,
        "cost_breakdown": cost_breakdown
    } 