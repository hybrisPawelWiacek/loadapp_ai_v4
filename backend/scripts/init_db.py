"""Database initialization script with default data."""
import json
import os
import sys
import uuid
from decimal import Decimal

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.infrastructure.database import SessionLocal, engine, Base
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.rate_models import RateValidationRuleModel
from backend.infrastructure.models.transport_models import (
    TransportTypeModel, TruckSpecificationModel,
    DriverSpecificationModel
)

from backend.scripts.seed_data import (
    RATE_VALIDATION_RULES,
    TRANSPORT_TYPES,
    BUSINESS_ENTITIES
)
from backend.scripts.seed_transports import seed_transports

def init_rate_validation_rules(db):
    """Initialize rate validation rules."""
    try:
        # Clear existing rules
        db.query(RateValidationRuleModel).delete()
        
        # Add new rules
        for rule in RATE_VALIDATION_RULES:
            model = RateValidationRuleModel(**rule)
            db.add(model)
        
        db.commit()
        print("Successfully initialized rate validation rules")
        
    except Exception as e:
        print(f"Error initializing rate validation rules: {e}")
        db.rollback()
        raise

def init_transport_types(db):
    """Initialize transport types."""
    try:
        # Only initialize if no transport types exist
        if db.query(TransportTypeModel).first():
            print("Transport types already initialized")
            return

        for type_data in TRANSPORT_TYPES:
            # Create specifications
            truck_specs = TruckSpecificationModel(
                id=str(uuid.uuid4()),
                **type_data["truck_specs"]
            )

            driver_specs = DriverSpecificationModel(
                id=str(uuid.uuid4()),
                **type_data["driver_specs"]
            )

            # Create transport type
            transport_type = TransportTypeModel(
                id=type_data["id"],
                name=type_data["name"],
                truck_specifications=truck_specs,
                driver_specifications=driver_specs
            )

            db.add(transport_type)

        db.commit()
        print("Successfully initialized transport types")

    except Exception as e:
        print(f"Error initializing transport types: {e}")
        db.rollback()
        raise

def init_business_entities(db):
    """Initialize business entities."""
    try:
        # Only initialize if no business entities exist
        if db.query(BusinessEntityModel).first():
            print("Business entities already initialized")
            return

        for entity_data in BUSINESS_ENTITIES:
            # Ensure all JSON fields are properly serialized
            entity = BusinessEntityModel(
                id=entity_data["id"],
                name=entity_data["name"],
                address=entity_data["address"],
                contact_info=entity_data["contact_info"],  # Model handles JSON conversion
                business_type=entity_data["business_type"],
                certifications=entity_data["certifications"],  # Model handles JSON conversion
                operating_countries=entity_data["operating_countries"],  # Model handles JSON conversion
                cost_overheads=entity_data["cost_overheads"],  # Model handles JSON conversion
                default_cost_settings=entity_data["default_cost_settings"],  # Model handles JSON conversion
                is_active=entity_data["is_active"]
            )
            db.add(entity)

        db.commit()
        print("Successfully initialized business entities")

    except Exception as e:
        print(f"Error initializing business entities: {e}")
        db.rollback()
        raise

def init_db():
    """Initialize database with all required data."""
    # Drop all tables first
    Base.metadata.drop_all(bind=engine)
    print("Dropped all existing tables")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

    # Create session
    db = SessionLocal()

    try:
        # Initialize all components in proper order
        init_rate_validation_rules(db)  # Initialize rates first
        init_transport_types(db)        # Then transport types
        init_business_entities(db)      # Then business entities
        seed_transports(db)            # Finally, create transport instances
        
        print("Database initialization completed successfully")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 