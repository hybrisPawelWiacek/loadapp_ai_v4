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
    container = get_container()
    
    try:
        # Get cost breakdown first
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
        try:
            offer = container.offer_service().create_offer(
                route_id=UUID(route_id),
                cost_breakdown_id=cost_breakdown.id,
                margin_percentage=margin_percentage,
                enhance_with_ai=enhance_with_ai
            )
            return jsonify({"offer": offer.to_dict()}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
            
    except Exception as e:
        logger.error("offer.generate.error",
                    route_id=route_id,
                    error=str(e))
        return jsonify({"error": str(e)}), 500


@offer_bp.route("/<offer_id>/enhance", methods=["POST"])
def enhance_offer(offer_id: str):
    """Enhance an existing offer with AI-generated content."""
    container = get_container()
    
    try:
        enhanced_offer = container.offer_service().enhance_offer(UUID(offer_id))
        if not enhanced_offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": enhanced_offer.to_dict()}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("offer.enhance.error",
                    offer_id=offer_id,
                    error=str(e))
        return jsonify({"error": f"Failed to enhance offer: {str(e)}"}), 500


@offer_bp.route("/<offer_id>", methods=["GET"])
def get_offer(offer_id: str):
    """Get an offer by ID."""
    container = get_container()
    
    try:
        # Get offer
        offer = container.offer_service().get_offer(UUID(offer_id))
        if not offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": offer.to_dict()}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("offer.get.error",
                    offer_id=offer_id,
                    error=str(e))
        return jsonify({"error": str(e)}), 500


@offer_bp.route("/<offer_id>/finalize", methods=["POST"])
def finalize_offer(offer_id: str):
    """Finalize an offer and update related entities."""
    container = get_container()
    
    try:
        # Try to finalize the offer
        finalized_offer = container.offer_service().finalize_offer(UUID(offer_id))
        if not finalized_offer:
            return jsonify({"error": "Offer not found"}), 404

        return jsonify({
            "status": "success",
            "message": "Offer finalized successfully",
            "offer": {
                "id": str(finalized_offer.id),
                "route_id": str(finalized_offer.route_id),
                "status": finalized_offer.status,
                "final_price": str(finalized_offer.final_price),
                "ai_content": finalized_offer.ai_content,
                "fun_fact": finalized_offer.fun_fact,
                "created_at": finalized_offer.created_at.isoformat()
            }
        }), 200

    except ValueError as e:
        # Business validation errors (invalid state, missing cargo, etc.)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("offer.finalize.error",
                    offer_id=offer_id,
                    error=str(e))
        return jsonify({"error": str(e)}), 500 