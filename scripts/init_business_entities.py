"""Script to initialize seed business entities in the database."""
import json
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.database import Base

# Create database engine
engine = create_engine('sqlite:///loadapp.db')
Session = sessionmaker(bind=engine)
session = Session()

# Seed data for three different business entities
business_entities = [
    {
        "id": str(uuid.uuid4()),
        "name": "EcoTrans GmbH",
        "address": "Hauptstraße 123, 10115 Berlin, Germany",
        "contact_info": {
            "email": "contact@ecotrans.de",
            "phone": "+49 30 123456",
            "website": "www.ecotrans.de"
        },
        "business_type": "carrier",
        "certifications": [
            "ISO 9001",
            "ISO 14001",  # Environmental management
            "GDP",        # Good Distribution Practice
            "SQAS"       # Safety & Quality Assessment System
        ],
        "operating_countries": ["DE", "PL", "CZ", "AT", "NL"],
        "cost_overheads": {
            "admin": "100.00",
            "insurance": "250.00",
            "eco_compliance": "180.00",
            "quality_management": "150.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.85",            # Slightly higher due to eco-friendly fuel
            "driver_base_rate": "200.00",   # Premium for qualified eco-drivers
            "toll_rate": "0.18",
            "enabled_components": ["fuel", "toll", "driver", "eco"]
        },
        "is_active": True
    },
    {
        "id": str(uuid.uuid4()),
        "name": "SpeedLog Express",
        "address": "Logistics Park 45, 00-001 Warsaw, Poland",
        "contact_info": {
            "email": "operations@speedlog.pl",
            "phone": "+48 22 987654",
            "website": "www.speedlog.pl"
        },
        "business_type": "logistics_provider",
        "certifications": [
            "ISO 9001",
            "AEO",        # Authorized Economic Operator
            "TAPA FSR"    # Security certification
        ],
        "operating_countries": ["PL", "DE", "CZ", "SK", "HU", "LT"],
        "cost_overheads": {
            "admin": "80.00",
            "insurance": "200.00",
            "security": "120.00",
            "tracking": "90.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.65",
            "driver_base_rate": "150.00",
            "toll_rate": "0.17",
            "enabled_components": ["fuel", "toll", "driver", "security"]
        },
        "is_active": True
    },
    {
        "id": str(uuid.uuid4()),
        "name": "HeavyHaul Solutions",
        "address": "Industrieweg 78, 3542 AD Utrecht, Netherlands",
        "contact_info": {
            "email": "info@heavyhaul.nl",
            "phone": "+31 30 789012",
            "website": "www.heavyhaul.nl"
        },
        "business_type": "specialized_transport",
        "certifications": [
            "ISO 9001",
            "DEKRA",          # Technical inspection certification
            "IMCA",           # Heavy lift certification
            "LEEA"            # Lifting Equipment Engineers Association
        ],
        "operating_countries": ["NL", "DE", "BE", "FR"],
        "cost_overheads": {
            "admin": "150.00",
            "insurance": "400.00",
            "special_equipment": "300.00",
            "permits": "250.00"
        },
        "default_cost_settings": {
            "fuel_rate": "2.00",             # Higher due to heavy loads
            "driver_base_rate": "250.00",    # Specialized driver premium
            "toll_rate": "0.25",             # Higher toll class
            "enabled_components": ["fuel", "toll", "driver", "permits", "special_equipment"]
        },
        "is_active": True
    }
]

def init_business_entities():
    """Initialize business entities in the database."""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Delete existing business entities
        session.query(BusinessEntityModel).delete()
        
        # Add new business entities
        for entity_data in business_entities:
            entity = BusinessEntityModel(
                id=entity_data["id"],
                name=entity_data["name"],
                address=entity_data["address"],
                contact_info=json.dumps(entity_data["contact_info"]),
                business_type=entity_data["business_type"],
                certifications=json.dumps(entity_data["certifications"]),
                operating_countries=json.dumps(entity_data["operating_countries"]),
                cost_overheads=json.dumps(entity_data["cost_overheads"]),
                default_cost_settings=json.dumps(entity_data["default_cost_settings"]),
                is_active=entity_data["is_active"]
            )
            session.add(entity)
        
        # Commit the changes
        session.commit()
        print("Successfully initialized business entities:")
        for entity in business_entities:
            print(f"- {entity['name']} ({entity['business_type']})")
            
    except Exception as e:
        print(f"Error initializing business entities: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_business_entities() 