"""Database configuration and base setup for SQLite."""
from sqlalchemy import create_engine, event, text, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
import os

# Default SQLite URL if no environment variable is set
SQLITE_URL = "sqlite:///backend/database/loadapp.db"

def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with optimal settings."""
    # Disable pysqlite's emitting of the BEGIN statement entirely
    dbapi_connection.isolation_level = None
    
    # Enable WAL mode and other optimizations
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def begin_transaction(conn):
    """Emit our own BEGIN transaction."""
    # Check if we're already in a transaction
    cursor = conn.connection.cursor()
    in_transaction = cursor.execute("SELECT 1 FROM sqlite_master LIMIT 1").connection.in_transaction
    if not in_transaction:
        conn.execute(text("BEGIN"))

# Create engine with SQLite optimizations
engine = create_engine(
    SQLITE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multi-threading for SQLite
        "isolation_level": None  # Handle transactions manually
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=True  # Log SQL queries (disable in production)
)

# Configure SQLite connection
event.listen(engine, "connect", configure_sqlite_connection)
event.listen(engine, "begin", begin_transaction)

# Create session factory with transaction management
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create scoped session for thread-safe access
db_session = scoped_session(SessionLocal)

# Create declarative base
Base = declarative_base()
Base.query = db_session.query_property()

def get_db():
    """Get database session."""
    try:
        return db_session
    finally:
        db_session.remove()

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
            connect_args={
                "check_same_thread": False,
                "isolation_level": None
            },
            poolclass=StaticPool
        )
        # Configure SQLite connection for the new engine
        event.listen(engine, "connect", configure_sqlite_connection)
        event.listen(engine, "begin", begin_transaction)
        
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
        transport_models,
        rate_models  # Ensure rate_models is imported
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Ensure proper file permissions
    db_path = database_url.replace('sqlite:///', '') if database_url else 'backend/database/loadapp.db'
    if os.path.exists(db_path):
        os.chmod(db_path, 0o666)  # rw-rw-rw- 

def get_database_path(database_url: str = None) -> str:
    """Get the database file path from the database URL."""
    db_path = database_url.replace('sqlite:///', '') if database_url else 'backend/database/loadapp.db'
    return db_path 