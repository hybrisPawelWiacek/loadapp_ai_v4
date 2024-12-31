"""Test configuration and shared fixtures."""
import os
import sys
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from flask import g
from dataclasses import dataclass

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.infrastructure.database import Base
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.cargo_models import CargoModel
from backend.infrastructure.models.transport_models import (
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
            URL=TEST_DATABASE_URL,
            ECHO=False,
            TRACK_MODIFICATIONS=False
        ),
        OPENAI=OpenAIConfig(
            API_KEY='test_key',
            MODEL='gpt-4-turbo-preview',
            MAX_RETRIES=3,
            RETRY_DELAY=0.1,
            TIMEOUT=5.0
        ),
        GOOGLE_MAPS=GoogleMapsConfig(
            API_KEY='test_key',
            MAX_RETRIES=3,
            RETRY_DELAY=0.1,
            TIMEOUT=5.0,
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
    return create_engine(TEST_DATABASE_URL)

@pytest.fixture(scope="function")
def tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db(engine, tables):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def app(test_config):
    """Create Flask test app with test database session."""
    app = create_app(test_config)
    
    @app.before_request
    def before_request():
        g.db = db_session
    
    return app

@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()

@pytest.fixture
def business_entity(db_session):
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
    db_session.add(entity)
    db_session.commit()
    return entity

@pytest.fixture
def cargo(db_session, business_entity):
    """Create a test cargo."""
    cargo = CargoModel(
        id=str(uuid.uuid4()),
        business_entity_id=business_entity.id,
        weight=1000.0,
        volume=2.5,
        cargo_type='general',
        value='1000.00',
        special_requirements=['temperature_controlled'],
        status='pending'
    )
    db_session.add(cargo)
    db_session.commit()
    return cargo 