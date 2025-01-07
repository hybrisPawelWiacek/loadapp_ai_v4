"""Business entity-related API routes."""
from typing import List
from flask import Blueprint, jsonify, g, request
import structlog
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from uuid import UUID

from ...domain.entities.business import BusinessEntity
from ...domain.services.business_service import BusinessService
from ...infrastructure.repositories.business_repository import SQLBusinessRepository

# Create blueprint
business_bp = Blueprint("business", __name__, url_prefix="/api/business")

# Configure logger
logger = structlog.get_logger()


def get_db():
    """Get database session."""
    if not hasattr(g, 'db'):
        logger.error("business_routes.get_db.error", error="Database session not initialized")
        raise RuntimeError("Database session not initialized")
    logger.debug("business_routes.get_db.success", session_id=id(g.db))
    return g.db


@business_bp.route("", methods=["GET"])
def list_businesses():
    """List all active business entities."""
    logger.info("business_routes.list_businesses.start")
    try:
        db = get_db()
        business_repo = SQLBusinessRepository(db)
        business_service = BusinessService(business_repo)
        
        businesses = business_service.list_active_businesses()
        return jsonify([b.to_dict() for b in businesses]), 200
        
    except (RuntimeError, SQLAlchemyError) as e:
        logger.error("business_routes.list_businesses.error", error=str(e))
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error("business_routes.list_businesses.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@business_bp.route("/<business_id>/overheads", methods=["PUT"])
def update_business_overheads(business_id: str):
    """Update business overhead costs."""
    logger.info("business_routes.update_overheads.start", business_id=business_id)
    try:
        # Get database session
        db = get_db()
        business_repo = SQLBusinessRepository(db)
        business_service = BusinessService(business_repo)
        
        # Get request data
        data = request.get_json()
        if not data or "cost_overheads" not in data:
            return jsonify({"error": "Missing cost_overheads in request"}), 400
            
        # Validate and convert overhead costs
        try:
            overheads = {
                k: Decimal(str(v))
                for k, v in data["cost_overheads"].items()
            }
        except (TypeError, ValueError) as e:
            return jsonify({"error": f"Invalid overhead cost value: {str(e)}"}), 400
            
        # Update business entity
        business = business_service.update_business_overheads(
            business_id=UUID(business_id),
            cost_overheads=overheads
        )
        
        if not business:
            return jsonify({"error": "Business entity not found"}), 404
            
        return jsonify(business.to_dict()), 200
        
    except ValueError as e:
        logger.error("business_routes.update_overheads.error", business_id=business_id, error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("business_routes.update_overheads.error", business_id=business_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@business_bp.route("", methods=["POST"])
def create_business():
    """Create new business entity (not implemented in PoC)."""
    logger.info("business_routes.create_business.not_implemented")
    return jsonify({"error": "Not implemented in PoC"}), 501


@business_bp.route("/<business_id>", methods=["GET"])
def get_business(business_id: str):
    """Get business entity by ID (not implemented in PoC)."""
    logger.info("business_routes.get_business.not_implemented", business_id=business_id)
    return jsonify({"error": "Not implemented in PoC"}), 501


@business_bp.route("/<business_id>", methods=["PUT"])
def update_business(business_id: str):
    """Update business entity (not implemented in PoC)."""
    logger.info("business_routes.update_business.not_implemented", business_id=business_id)
    return jsonify({"error": "Not implemented in PoC"}), 501


@business_bp.route("/<business_id>/validate", methods=["POST"])
def validate_business(business_id: str):
    """Validate business entity (not implemented in PoC)."""
    logger.info("business_routes.validate_business.not_implemented", business_id=business_id)
    return jsonify({"error": "Not implemented in PoC"}), 501 