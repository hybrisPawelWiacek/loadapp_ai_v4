"""Transport-related API routes."""
from flask import Blueprint, jsonify, current_app, g
from sqlalchemy.orm import Session

from ...infrastructure.database import SessionLocal
from ...infrastructure.models.transport_models import TransportTypeModel

# Create blueprint
transport_bp = Blueprint("transport", __name__, url_prefix="/api/transport")


def get_db():
    """Get database session."""
    if hasattr(g, 'db'):
        return g.db
    
    if not hasattr(g, '_db'):
        g._db = SessionLocal()
    return g._db


@transport_bp.teardown_app_request
def teardown_db(exception=None):
    """Close database session at the end of request."""
    db = g.pop('_db', None)
    if db is not None:
        db.close()


@transport_bp.route("/types", methods=["GET"])
def list_transport_types():
    """List all available transport types."""
    db = get_db()
    try:
        types = db.query(TransportTypeModel).all()
        
        return jsonify([
            {
                "id": t.id,
                "name": t.name,
                "truck_specifications": {
                    "fuel_consumption_empty": t.truck_specifications.fuel_consumption_empty,
                    "fuel_consumption_loaded": t.truck_specifications.fuel_consumption_loaded,
                    "toll_class": t.truck_specifications.toll_class,
                    "euro_class": t.truck_specifications.euro_class,
                    "co2_class": t.truck_specifications.co2_class,
                    "maintenance_rate_per_km": float(t.truck_specifications.maintenance_rate_per_km)
                },
                "driver_specifications": {
                    "daily_rate": float(t.driver_specifications.daily_rate),
                    "required_license_type": t.driver_specifications.required_license_type,
                    "required_certifications": t.driver_specifications.get_certifications()
                }
            }
            for t in types
        ])
    except Exception as e:
        db.rollback()
        raise e


@transport_bp.route("/types/<type_id>", methods=["GET"])
def get_transport_type(type_id: str):
    """Get a specific transport type by ID."""
    db = get_db()
    try:
        transport_type = db.query(TransportTypeModel).filter_by(id=type_id).first()
        
        if not transport_type:
            return jsonify({"error": "Transport type not found"}), 404
        
        return jsonify({
            "id": transport_type.id,
            "name": transport_type.name,
            "truck_specifications": {
                "fuel_consumption_empty": transport_type.truck_specifications.fuel_consumption_empty,
                "fuel_consumption_loaded": transport_type.truck_specifications.fuel_consumption_loaded,
                "toll_class": transport_type.truck_specifications.toll_class,
                "euro_class": transport_type.truck_specifications.euro_class,
                "co2_class": transport_type.truck_specifications.co2_class,
                "maintenance_rate_per_km": float(transport_type.truck_specifications.maintenance_rate_per_km)
            },
            "driver_specifications": {
                "daily_rate": float(transport_type.driver_specifications.daily_rate),
                "required_license_type": transport_type.driver_specifications.required_license_type,
                "required_certifications": transport_type.driver_specifications.get_certifications()
            }
        })
    except Exception as e:
        db.rollback()
        raise e 