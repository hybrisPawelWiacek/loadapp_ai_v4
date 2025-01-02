"""Offer-related API routes."""
from decimal import Decimal
from uuid import UUID
from flask import Blueprint, jsonify, request, g, current_app
from flask_restful import Api
import structlog

from ...domain.entities.cargo import CostBreakdown
from ...domain.services.offer_service import OfferService
from ...infrastructure.models.route_models import RouteModel
from ...infrastructure.repositories.route_repository import SQLRouteRepository
from ...infrastructure.repositories.cargo_repository import SQLCostBreakdownRepository, SQLOfferRepository, SQLCargoRepository
from ...infrastructure.adapters.openai_adapter import OpenAIAdapter


# Create blueprint
offer_bp = Blueprint("offer", __name__, url_prefix="/api/offer")
api = Api(offer_bp)

# Configure logger
logger = structlog.get_logger()


def get_container():
    """Get the container from the request context."""
    if not hasattr(g, 'container'):
        raise RuntimeError("Application container not initialized")
    return g.container


@offer_bp.route("/generate/<route_id>", methods=["POST"])
def generate_offer(route_id: str):
    """Generate an offer for a route."""
    data = request.get_json()
    db = g.db
    
    try:
        # Get container
        container = get_container()
        
        # Get route
        route = container.route_repository().find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get cost breakdown
        cost_breakdown = container.cost_breakdown_repository().find_by_route_id(UUID(route_id))
        if not cost_breakdown:
            return jsonify({"error": "Cost breakdown not found for route"}), 404

        # Get margin percentage
        try:
            margin_percentage = Decimal(data.get("margin_percentage", "15.0"))
            if margin_percentage < 0:
                return jsonify({"error": "Invalid margin percentage"}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid margin percentage format"}), 400

        # Generate offer
        enhance_with_ai = data.get("enhance_with_ai", False)
        offer = container.offer_service().create_offer(
            route_id=UUID(route_id),
            cost_breakdown_id=cost_breakdown.id,
            margin_percentage=margin_percentage,
            enhance_with_ai=enhance_with_ai
        )
        
        return jsonify({"offer": offer.to_dict()}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@offer_bp.route("/<offer_id>/enhance", methods=["POST"])
def enhance_offer(offer_id: str):
    """Enhance an existing offer with AI-generated content."""
    db = g.db
    
    try:
        # Get container
        container = get_container()
        
        # Enhance offer
        enhanced_offer = container.offer_service().enhance_offer(UUID(offer_id))
        if not enhanced_offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": enhanced_offer.to_dict()}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to enhance offer: {str(e)}"}), 500


@offer_bp.route("/<offer_id>", methods=["GET"])
def get_offer(offer_id: str):
    """Get an offer by ID."""
    try:
        # Get container
        container = get_container()
        
        # Get offer
        offer = container.offer_service().get_offer(UUID(offer_id))
        if not offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": offer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 


@offer_bp.route("/<offer_id>/finalize", methods=["POST"])
def finalize_offer(offer_id: str):
    """Finalize an offer and update related entities.
    
    Args:
        offer_id: ID of the offer to finalize
        
    Returns:
        JSON response with success/error message
    """
    container = get_container()
    db = g.db
    
    try:
        # First check if offer exists
        offer = container.offer_service().get_offer(UUID(offer_id))
        if not offer:
            return jsonify({"error": "Offer not found"}), 404

        # Try to finalize the offer
        try:
            finalized_offer = container.offer_service().finalize_offer(UUID(offer_id))
            
            # Log operation
            logger.info("offer.finalized",
                       offer_id=str(offer_id),
                       route_id=str(finalized_offer.route_id),
                       status="finalized")

            return jsonify({
                "status": "success",
                "message": "Offer finalized successfully",
                "offer": finalized_offer.to_dict()
            }), 200

        except ValueError as e:
            db.rollback()
            if "Route has no cargo assigned" in str(e):
                return jsonify({"error": str(e)}), 404
            return jsonify({"error": str(e)}), 400

    except Exception as e:
        db.rollback()
        logger.error("offer.finalize.error",
                    offer_id=offer_id,
                    error=str(e))
        return jsonify({"error": "Failed to finalize offer"}), 500 