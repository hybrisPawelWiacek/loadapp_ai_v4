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