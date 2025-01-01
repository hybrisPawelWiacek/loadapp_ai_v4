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
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db(engine):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def app(test_config, db):
    """Create Flask test app with test database session."""
    app = create_app(test_config)
    
    @app.before_request
    def before_request():
        g.db = db
    
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
    return entity 