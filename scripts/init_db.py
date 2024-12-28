"""Database initialization script with default data."""
from decimal import Decimal
import os
import sys
import uuid

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.infrastructure.database import SessionLocal, engine, Base
from backend.infrastructure.models.transport_models import (
    TransportTypeModel, TruckSpecificationModel,
    DriverSpecificationModel
)


def init_db():
    """Initialize database with default data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        # Check if we already have transport types
        if db.query(TransportTypeModel).first():
            print("Database already initialized")
            return

        # Create default transport types
        transport_types = [
            {
                "id": "flatbed",
                "name": "Flatbed Truck",
                "truck_specs": {
                    "fuel_consumption_empty": 0.22,
                    "fuel_consumption_loaded": 0.29,
                    "toll_class": "4-axle",
                    "euro_class": "EURO6",
                    "co2_class": "A",
                    "maintenance_rate_per_km": "0.15"
                },
                "driver_specs": {
                    "daily_rate": "138.00",
                    "required_license_type": "CE",
                    "required_certifications": ["ADR"]
                }
            },
            {
                "id": "container",
                "name": "Container Truck",
                "truck_specs": {
                    "fuel_consumption_empty": 0.24,
                    "fuel_consumption_loaded": 0.32,
                    "toll_class": "5-axle",
                    "euro_class": "EURO6",
                    "co2_class": "B",
                    "maintenance_rate_per_km": "0.18"
                },
                "driver_specs": {
                    "daily_rate": "142.00",
                    "required_license_type": "CE",
                    "required_certifications": ["Container", "ADR"]
                }
            },
            {
                "id": "livestock",
                "name": "Livestock Carrier",
                "truck_specs": {
                    "fuel_consumption_empty": 0.25,
                    "fuel_consumption_loaded": 0.33,
                    "toll_class": "4-axle",
                    "euro_class": "EURO6",
                    "co2_class": "B",
                    "maintenance_rate_per_km": "0.20"
                },
                "driver_specs": {
                    "daily_rate": "145.00",
                    "required_license_type": "CE",
                    "required_certifications": ["Livestock", "Animal welfare"]
                }
            },
            {
                "id": "plandeka",
                "name": "Tautliner",
                "truck_specs": {
                    "fuel_consumption_empty": 0.23,
                    "fuel_consumption_loaded": 0.30,
                    "toll_class": "4-axle",
                    "euro_class": "EURO6",
                    "co2_class": "A",
                    "maintenance_rate_per_km": "0.16"
                },
                "driver_specs": {
                    "daily_rate": "140.00",
                    "required_license_type": "CE",
                    "required_certifications": ["ADR"]
                }
            },
            {
                "id": "oversized",
                "name": "Oversized Transport",
                "truck_specs": {
                    "fuel_consumption_empty": 0.35,
                    "fuel_consumption_loaded": 0.45,
                    "toll_class": "special",
                    "euro_class": "EURO6",
                    "co2_class": "C",
                    "maintenance_rate_per_km": "0.25"
                },
                "driver_specs": {
                    "daily_rate": "160.00",
                    "required_license_type": "CE",
                    "required_certifications": ["Oversized", "Special transport"]
                }
            }
        ]

        # Create and save transport types
        for type_data in transport_types:
            # Create specifications
            truck_specs = TruckSpecificationModel(
                id=str(uuid.uuid4()),
                fuel_consumption_empty=type_data["truck_specs"]["fuel_consumption_empty"],
                fuel_consumption_loaded=type_data["truck_specs"]["fuel_consumption_loaded"],
                toll_class=type_data["truck_specs"]["toll_class"],
                euro_class=type_data["truck_specs"]["euro_class"],
                co2_class=type_data["truck_specs"]["co2_class"],
                maintenance_rate_per_km=type_data["truck_specs"]["maintenance_rate_per_km"]
            )

            driver_specs = DriverSpecificationModel(
                id=str(uuid.uuid4()),
                daily_rate=type_data["driver_specs"]["daily_rate"],
                required_license_type=type_data["driver_specs"]["required_license_type"],
                required_certifications=type_data["driver_specs"]["required_certifications"]
            )

            # Create transport type
            transport_type = TransportTypeModel(
                id=type_data["id"],
                name=type_data["name"],
                truck_specifications=truck_specs,
                driver_specifications=driver_specs
            )

            db.add(transport_type)

        # Commit changes
        db.commit()
        print("Database initialized with default transport types")

    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db() 