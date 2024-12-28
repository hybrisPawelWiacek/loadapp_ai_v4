"""Database configuration and base setup for SQLite."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# SQLite URL with file path
SQLITE_URL = "sqlite:///loadapp.db"

# Create engine with SQLite optimizations
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},  # Allow multi-threading for SQLite
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=True  # Log SQL queries (disable in production)
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(database_url: str = None):
    """Initialize database with all models.
    
    Args:
        database_url: Optional database URL. If not provided, uses default SQLite URL.
    """
    global engine, SessionLocal
    
    if database_url:
        # Create new engine with provided URL
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        # Update session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    
    # Import all models to ensure they're registered with Base
    from ..infrastructure.models import (
        business_models,
        cargo_models,
        route_models,
        transport_models
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine) 