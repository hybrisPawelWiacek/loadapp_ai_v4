"""Transport-related API routes."""
from flask import Blueprint, jsonify, request, g
from uuid import UUID
import structlog

from ...domain.services.transport_service import TransportService

# Create blueprint
transport_bp = Blueprint("transport", __name__, url_prefix="/api/transport")

# Configure logger
logger = structlog.get_logger()


def get_container():
    """Get the container from the request context."""
    if not hasattr(g, 'container'):
        raise RuntimeError("Application container not initialized")
    return g.container


@transport_bp.route("/types", methods=["GET"])
def list_transport_types():
    """List all available transport types."""
    container = get_container()
    try:
        types = container.transport_service().get_transport_types()
        return jsonify([t.dict() for t in types]), 200
    except Exception as e:
        logger.error("transport.types.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/types/<type_id>", methods=["GET"])
def get_transport_type(type_id: str):
    """Get a specific transport type."""
    container = get_container()
    try:
        transport_type = container.transport_service().get_transport_type(type_id)
        if not transport_type:
            return jsonify({"error": "Transport type not found"}), 404
        return jsonify(transport_type.dict()), 200
    except Exception as e:
        logger.error("transport.type.error", type_id=type_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/business/<business_id>/transports", methods=["GET"])
def list_business_transports(business_id: str):
    """List all transports for a business entity."""
    container = get_container()
    try:
        logger.info("transport.business.start", business_id=business_id)
        transports = container.transport_service().get_business_transports(UUID(business_id))
        logger.info("transport.business.success", business_id=business_id, transport_count=len(transports))
        return jsonify([t.dict() for t in transports]), 200
    except ValueError as e:
        logger.error("transport.business.error", business_id=business_id, error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("transport.business.error", business_id=business_id, error=str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/create", methods=["POST"])
def create_transport():
    """Create a new transport."""
    container = get_container()
    data = request.get_json()

    try:
        transport_type_id = data.get("transport_type_id")
        business_entity_id = data.get("business_entity_id")

        if not transport_type_id or not business_entity_id:
            return jsonify({"error": "Missing required fields"}), 400

        transport = container.transport_service().create_transport(
            transport_type_id=transport_type_id,
            business_entity_id=UUID(business_entity_id)
        )
        return jsonify(transport.dict()), 201

    except ValueError as e:
        logger.error("transport.create.error", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("transport.create.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/<transport_id>", methods=["GET"])
def get_transport(transport_id: str):
    """Get a transport by ID."""
    container = get_container()
    try:
        transport = container.transport_service().get_transport(UUID(transport_id))
        if not transport:
            return jsonify({"error": "Transport not found"}), 404
        return jsonify(transport.dict()), 200
    except ValueError as e:
        logger.error("transport.get.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("transport.get.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/<transport_id>/deactivate", methods=["POST"])
def deactivate_transport(transport_id: str):
    """Deactivate a transport."""
    container = get_container()
    try:
        transport = container.transport_service().deactivate_transport(UUID(transport_id))
        return jsonify({
            "message": "Transport deactivated successfully",
            "transport": transport.dict()
        }), 200
    except ValueError as e:
        logger.error("transport.deactivate.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("transport.deactivate.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@transport_bp.route("/<transport_id>/reactivate", methods=["POST"])
def reactivate_transport(transport_id: str):
    """Reactivate a transport."""
    container = get_container()
    try:
        transport = container.transport_service().reactivate_transport(UUID(transport_id))
        return jsonify({
            "message": "Transport reactivated successfully",
            "transport": transport.dict()
        }), 200
    except ValueError as e:
        logger.error("transport.reactivate.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("transport.reactivate.error", transport_id=transport_id, error=str(e))
        return jsonify({"error": str(e)}), 500 