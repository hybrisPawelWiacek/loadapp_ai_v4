"""Test configuration and shared fixtures."""
from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / 'backend'
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from backend.config import (
    Config, ServerConfig, DatabaseConfig,
    OpenAIConfig, GoogleMapsConfig, LoggingConfig,
    FrontendConfig
)
from backend.infrastructure.database import Base
# Import all models to ensure they are registered with SQLAlchemy
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.cargo_models import (
    CargoModel, CostSettingsModel,
    CostBreakdownModel, OfferModel
)
from backend.infrastructure.models.route_models import (
    RouteModel, LocationModel, TimelineEventModel,
    CountrySegmentModel, EmptyDrivingModel
)
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)


@pytest.fixture
def test_config() -> Config:
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
            API_KEY='test-openai-key',
            MODEL='gpt-4o-mini',
            MAX_RETRIES=1,
            RETRY_DELAY=0.1,
            TIMEOUT=1.0
        ),
        GOOGLE_MAPS=GoogleMapsConfig(
            API_KEY='test-gmaps-key',
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
    # Use SQLite in-memory database for tests
    engine = create_engine("sqlite:///:memory:")
    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    # Rollback the transaction and close connections
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db(test_config: Config) -> Session:
    """Create a test database session."""
    # Create engine and tables
    engine = create_engine(test_config.DATABASE.URL)
    Base.metadata.create_all(engine)

    # Create session
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(engine) 