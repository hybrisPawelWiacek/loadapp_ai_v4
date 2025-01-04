"""Business entity-related API routes."""
from typing import List
from flask import Blueprint, jsonify, g
import structlog
from sqlalchemy.exc import SQLAlchemyError

from ...domain.entities.business import BusinessEntity
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
        logger.debug("business_routes.list_businesses.query", filters={"is_active": True})
        businesses = business_repo.find_all(filters={"is_active": True})
        
        logger.info("business_routes.list_businesses.success", count=len(businesses))
        return jsonify([b.to_dict() for b in businesses]), 200
        
    except RuntimeError as e:
        logger.error("business_routes.list_businesses.error", error="Database session not initialized")
        return jsonify({"error": "Database error: session not initialized"}), 500
    except SQLAlchemyError as e:
        logger.error("business_routes.list_businesses.error", error=str(e))
        if hasattr(db, 'rollback'):
            db.rollback()
            logger.info("business_routes.list_businesses.rollback")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error("business_routes.list_businesses.error", error=str(e))
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