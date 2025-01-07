"""Cargo-related API routes."""
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4
from flask import Blueprint, jsonify, request, g
import structlog

from ...domain.entities.cargo import Cargo
from ...infrastructure.models.cargo_models import CargoStatusHistoryModel
from ...infrastructure.container import get_container

# Create blueprint
cargo_bp = Blueprint("cargo", __name__, url_prefix="/api/cargo")

# Configure logger
logger = structlog.get_logger()


def get_db():
    """Get database session."""
    if not hasattr(g, 'db'):
        raise RuntimeError("Database session not initialized")
    return g.db


@cargo_bp.route("", methods=["POST"])
def create_cargo():
    """Create new cargo entry."""
    data = request.get_json()
    
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        business_service = container.business_service()
        
        # Validate value format
        try:
            value = Decimal(str(data["value"]))
            if value <= 0:
                return jsonify({"error": "Value must be positive"}), 400
        except (TypeError, ValueError, InvalidOperation):
            return jsonify({"error": "Invalid value format"}), 400
            
        # Validate measurements
        if data.get("weight", 0) <= 0:
            return jsonify({"error": "Weight must be positive"}), 400
        if data.get("volume", 0) <= 0:
            return jsonify({"error": "Volume must be positive"}), 400

        # Mock certification validation (PoC implementation)
        business_service.validate_certifications(
            cargo_type=data["cargo_type"],
            business_entity_id=UUID(data["business_entity_id"])
        )
        
        # Create cargo entity
        cargo = Cargo(
            id=uuid4(),
            business_entity_id=UUID(data["business_entity_id"]),
            weight=float(data["weight"]),
            volume=float(data["volume"]),
            cargo_type=data["cargo_type"],
            value=value,
            special_requirements=data.get("special_requirements", [])
        )
        
        # Create cargo using service
        saved_cargo = cargo_service.create_cargo(cargo)
        
        # Log cargo creation
        logger.info(
            "cargo.created",
            cargo_id=str(saved_cargo.id),
            business_entity_id=str(saved_cargo.business_entity_id),
            cargo_type=saved_cargo.cargo_type,
            status=saved_cargo.status,
            validation="Certification and country validations are mocked for PoC"
        )
        
        return jsonify(saved_cargo.to_dict()), 201
        
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.create.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["GET"])
def get_cargo(cargo_id: str):
    """Get cargo details."""
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Get cargo
        cargo = cargo_service.get_cargo(UUID(cargo_id))
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
        
        # Log retrieval
        logger.info("cargo.retrieved", cargo_id=cargo_id)
        
        return jsonify(cargo.to_dict()), 200
        
    except ValueError:
        return jsonify({"error": "Invalid cargo ID format"}), 400
    except Exception as e:
        logger.error("cargo.retrieve.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("", methods=["GET"])
def list_cargo():
    """List cargo entries with pagination."""
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Get pagination parameters
        page = int(request.args.get("page", 1))
        size = min(int(request.args.get("size", 10)), 100)  # Limit max size to 100
        
        # Get business entity filter
        business_entity_id = request.args.get("business_entity_id")
        if business_entity_id:
            business_entity_id = UUID(business_entity_id)
        
        # Get cargo list
        result = cargo_service.list_cargo(
            business_entity_id=business_entity_id,
            page=page,
            size=size
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.list.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["PUT"])
def update_cargo(cargo_id: str):
    """Update cargo details."""
    data = request.get_json()
    
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Prepare update data
        update_data = {}
        
        # Validate and prepare numeric fields
        if "weight" in data:
            if float(data["weight"]) <= 0:
                return jsonify({"error": "Weight must be positive"}), 400
            update_data["weight"] = float(data["weight"])
            
        if "volume" in data:
            if float(data["volume"]) <= 0:
                return jsonify({"error": "Volume must be positive"}), 400
            update_data["volume"] = float(data["volume"])
            
        if "value" in data:
            try:
                value = Decimal(str(data["value"]))
                if value <= 0:
                    return jsonify({"error": "Value must be positive"}), 400
                update_data["value"] = value
            except (TypeError, ValueError, InvalidOperation):
                return jsonify({"error": "Invalid value format"}), 400
                
        # Add other fields
        if "cargo_type" in data:
            update_data["cargo_type"] = data["cargo_type"]
        if "special_requirements" in data:
            update_data["special_requirements"] = data["special_requirements"]
        if "status" in data:
            update_data["status"] = data["status"]
            
        # Update cargo
        updated_cargo = cargo_service.update_cargo(UUID(cargo_id), update_data)
        
        # Log update
        logger.info(
            "cargo.updated",
            cargo_id=cargo_id,
            status=updated_cargo.status,
            updated_fields=list(update_data.keys())
        )
        
        return jsonify(updated_cargo.to_dict()), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.update.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["DELETE"])
def delete_cargo(cargo_id: str):
    """Delete cargo entry."""
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Delete cargo
        cargo_service.delete_cargo(UUID(cargo_id))
        
        # Log deletion
        logger.info("cargo.deleted", cargo_id=cargo_id)
        
        return "", 204
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.delete.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>/status-history", methods=["GET"])
def get_cargo_status_history(cargo_id: str):
    """Get cargo status change history."""
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Get cargo to verify it exists
        cargo = cargo_service.get_cargo(UUID(cargo_id))
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
            
        # Get status history from model
        cargo_model = cargo_service.cargo_repository.get(cargo_id)
        history = cargo_model.status_history.order_by(CargoStatusHistoryModel.timestamp.desc()).all()
        
        # Format response
        history_data = [entry.to_dict() for entry in history]
        
        return jsonify({
            "cargo_id": cargo_id,
            "current_status": cargo.status,
            "history": history_data
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.status_history.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>/finalize-offer", methods=["POST"])
def finalize_offer(cargo_id: str):
    """Handle offer finalization for cargo."""
    data = request.get_json()
    
    try:
        # Get container
        container = get_container()
        cargo_service = container.cargo_service()
        
        # Validate offer ID
        if "offer_id" not in data:
            return jsonify({"error": "Missing offer_id"}), 400
            
        # Handle finalization
        cargo_service.handle_offer_finalization(
            cargo_id=UUID(cargo_id),
            offer_id=UUID(data["offer_id"])
        )
        
        # Log finalization
        logger.info(
            "cargo.offer_finalized",
            cargo_id=cargo_id,
            offer_id=data["offer_id"]
        )
        
        return jsonify({"message": "Offer finalized successfully"}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.finalize_offer.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500 