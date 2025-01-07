"""Script to seed transport instances for each business entity."""
import sys
import os
import uuid
from decimal import Decimal

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.infrastructure.database import SessionLocal, engine
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.business_models import BusinessEntityModel

def seed_transports(db=None):
    """Seed transport instances for each business entity."""
    if db is None:
        db = SessionLocal()
        should_close_db = True
    else:
        should_close_db = False
    
    try:
        # Only seed if no transports exist
        if db.query(TransportModel).first():
            print("Transports already seeded")
            return
            
        # Get all business entities
        business_entities = db.query(BusinessEntityModel).all()
        
        # Get all transport types
        transport_types = db.query(TransportTypeModel).all()
        
        # For each business entity, create multiple transports
        for business_entity in business_entities:
            print(f"Creating transports for {business_entity.name}")
            
            # Create 2 transports of each type for each business entity
            for transport_type in transport_types:
                for _ in range(2):
                    # Create new specifications (copying from transport type)
                    truck_specs = TruckSpecificationModel(
                        id=str(uuid.uuid4()),
                        fuel_consumption_empty=transport_type.truck_specifications.fuel_consumption_empty,
                        fuel_consumption_loaded=transport_type.truck_specifications.fuel_consumption_loaded,
                        toll_class=transport_type.truck_specifications.toll_class,
                        euro_class=transport_type.truck_specifications.euro_class,
                        co2_class=transport_type.truck_specifications.co2_class,
                        maintenance_rate_per_km=transport_type.truck_specifications.maintenance_rate_per_km
                    )
                    
                    driver_specs = DriverSpecificationModel(
                        id=str(uuid.uuid4()),
                        daily_rate=transport_type.driver_specifications.daily_rate,
                        driving_time_rate=transport_type.driver_specifications.driving_time_rate,
                        required_license_type=transport_type.driver_specifications.required_license_type,
                        required_certifications=transport_type.driver_specifications.required_certifications
                    )
                    
                    # Add specifications to session
                    db.add(truck_specs)
                    db.add(driver_specs)
                    db.flush()  # Ensure IDs are generated
                    
                    # Create transport instance
                    transport = TransportModel(
                        id=str(uuid.uuid4()),
                        transport_type_id=transport_type.id,
                        business_entity_id=business_entity.id,
                        truck_specifications_id=truck_specs.id,
                        driver_specifications_id=driver_specs.id,
                        is_active=True
                    )
                    
                    db.add(transport)
                    print(f"Created transport {transport.id} of type {transport_type.name}")
            
        db.commit()
        print("Successfully seeded transport instances")
        
    except Exception as e:
        print(f"Error seeding transports: {e}")
        db.rollback()
        raise
    finally:
        if should_close_db:
            db.close()

if __name__ == "__main__":
    seed_transports() 