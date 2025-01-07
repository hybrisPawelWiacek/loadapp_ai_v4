"""Location-related API routes."""
import logging
from uuid import UUID
from flask import Blueprint, jsonify, request, g

from ...infrastructure.container import get_container

logger = logging.getLogger(__name__)

# Create blueprint
location_bp = Blueprint("location", __name__, url_prefix="/api/location")


@location_bp.route("", methods=["POST"])
def create_location():
    """Create a new location."""
    data = request.get_json()
    db = g.db
    
    try:
        # Get container
        container = get_container()
        location_service = container.location_service()
        
        # Validate required fields
        if not data.get('address'):
            return jsonify({"error": "Address is required"}), 400
            
        # Create location
        location = location_service.create_location(data['address'])
        
        # Convert to response format
        response = {
            "id": str(location.id),
            "address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude
        }
        
        return jsonify(response), 201
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create location: {str(e)}")
        return jsonify({"error": "Failed to create location"}), 500
    finally:
        db.close()


@location_bp.route("/<location_id>", methods=["GET"])
def get_location(location_id):
    """Get location by ID."""
    db = g.db
    
    try:
        # Get container
        container = get_container()
        location_service = container.location_service()
        
        # Get location
        location = location_service.get_location(UUID(location_id))
        if not location:
            return jsonify({"error": "Location not found"}), 404
            
        # Convert to response format
        response = {
            "id": str(location.id),
            "address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to get location: {str(e)}")
        return jsonify({"error": "Failed to get location"}), 500
    finally:
        db.close()


@location_bp.route("/validate", methods=["POST"])
def validate_location():
    """Validate a location address."""
    data = request.get_json()
    db = g.db
    
    try:
        # Get container
        container = get_container()
        location_service = container.location_service()
        
        # Validate required fields
        if not data.get('address'):
            return jsonify({"error": "Address is required"}), 400
            
        # Validate location
        validation_result = location_service.validate_location(data['address'])
        return jsonify(validation_result), 200
        
    except Exception as e:
        logger.error(f"Location validation error: {str(e)}")
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 200
    finally:
        db.close() 