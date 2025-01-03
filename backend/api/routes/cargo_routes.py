"""Cargo-related API routes."""
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4
from flask import Blueprint, jsonify, request, g
from typing import Dict, Any, Optional
import structlog

from ...domain.entities.cargo import Cargo
from ...infrastructure.models.cargo_models import CargoModel
from ...infrastructure.repositories.cargo_repository import SQLCargoRepository
from ...infrastructure.repositories.business_repository import SQLBusinessRepository
from ...domain.services.route_service import RouteService

# Create blueprint
cargo_bp = Blueprint("cargo", __name__, url_prefix="/api/cargo")

# Configure logger
logger = structlog.get_logger()

# Define valid status transitions
VALID_STATUS_TRANSITIONS = {
    "pending": ["in_transit", "cancelled"],
    "in_transit": ["delivered", "cancelled"],
    "delivered": [],  # Terminal state
    "cancelled": []   # Terminal state
}


def get_db():
    """Get database session."""
    if not hasattr(g, 'db'):
        raise RuntimeError("Database session not initialized")
    return g.db


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if a status transition is allowed.
    
    Args:
        current_status: Current cargo status
        new_status: Requested new status
        
    Returns:
        bool: True if transition is valid
    """
    if current_status not in VALID_STATUS_TRANSITIONS:
        return False
    return new_status in VALID_STATUS_TRANSITIONS[current_status]


def log_cargo_operation(operation: str, cargo_id: str, details: Dict[str, Any] = None):
    """Log cargo operations with structured logging.
    
    Args:
        operation: Type of operation (create, update, delete, etc.)
        cargo_id: ID of the cargo
        details: Additional operation details
    """
    log_data = {
        "cargo_id": cargo_id,
        "operation": operation,
        **(details or {})
    }
    logger.info("cargo.operation", **log_data)


@cargo_bp.route("", methods=["POST"])
def create_cargo():
    """Create new cargo entry."""
    data = request.get_json()
    db = get_db()
    
    try:
        # Get business entity service
        business_service = get_container().business_service()
        
        # Validate business entity exists and is active
        business_repo = SQLBusinessRepository(db)
        business_entity = business_repo.find_by_id(UUID(data["business_entity_id"]))
        if not business_entity:
            return jsonify({"error": "Business entity not found"}), 404
        if not business_entity.is_active:
            return jsonify({"error": "Business entity is not active"}), 409
            
        # Mock certification validation (PoC implementation)
        business_service.validate_certifications(
            cargo_type=data["cargo_type"],
            business_entity_id=UUID(data["business_entity_id"])
        )
        
        # Mock operating countries validation will be done during route creation
        # as we don't have route countries at this point
        
        # Validate cargo data
        try:
            value = Decimal(str(data["value"]))
            if value <= 0:
                return jsonify({"error": "Value must be positive"}), 400
        except (TypeError, ValueError, InvalidOperation):
            return jsonify({"error": "Invalid value format"}), 400
            
        if data.get("weight", 0) <= 0:
            return jsonify({"error": "Weight must be positive"}), 400
            
        if data.get("volume", 0) <= 0:
            return jsonify({"error": "Volume must be positive"}), 400

        # Create cargo
        cargo = Cargo(
            id=uuid4(),
            business_entity_id=UUID(data["business_entity_id"]),
            weight=float(data["weight"]),
            volume=float(data["volume"]),
            cargo_type=data["cargo_type"],
            value=value,
            special_requirements=data.get("special_requirements", []),
            status="pending"  # Default status for new cargo
        )
        
        cargo_repo = SQLCargoRepository(db)
        saved_cargo = cargo_repo.save(cargo)
        
        # Log cargo creation with mock validation info
        log_cargo_operation(
            "create",
            str(saved_cargo.id),
            {
                "business_entity_id": str(saved_cargo.business_entity_id),
                "cargo_type": saved_cargo.cargo_type,
                "status": saved_cargo.status,
                "mock_validation": "Certification and country validations are mocked for PoC"
            }
        )
        
        return jsonify(saved_cargo.to_dict()), 201
        
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        logger.error("cargo.create.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["GET"])
def get_cargo(cargo_id: str):
    """Get cargo details."""
    db = get_db()
    
    try:
        cargo_repo = SQLCargoRepository(db)
        cargo = cargo_repo.find_by_id(UUID(cargo_id))
        
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
        
        # Log cargo retrieval
        log_cargo_operation("retrieve", cargo_id)
        
        return jsonify(cargo.to_dict()), 200
        
    except ValueError:
        return jsonify({"error": "Invalid cargo ID format"}), 400
    except Exception as e:
        logger.error("cargo.retrieve.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("", methods=["GET"])
def list_cargo():
    """List cargo entries with pagination."""
    db = get_db()
    
    try:
        # Get pagination parameters
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 10))
        
        # Get optional business entity filter
        business_entity_id = request.args.get("business_entity_id")
        filters = {}
        if business_entity_id:
            filters["business_entity_id"] = str(UUID(business_entity_id))
        
        # Validate pagination parameters
        if page < 1:
            return jsonify({"error": "Page must be positive"}), 400
        if size < 1 or size > 100:
            return jsonify({"error": "Size must be between 1 and 100"}), 400
        
        # Get cargo entries
        cargo_repo = SQLCargoRepository(db)
        result = cargo_repo.find_all_paginated(page=page, size=size, **filters)
        
        # Convert models to domain entities
        items = [cargo_repo._to_domain(item) for item in result["items"]]
        
        # Log cargo listing
        log_cargo_operation(
            "list",
            None,
            {
                "page": page,
                "size": size,
                "total": result["total"],
                "business_entity_id": business_entity_id
            }
        )
        
        # Convert to response format
        response = {
            "items": [cargo.to_dict() for cargo in items],
            "total": result["total"],
            "page": page,
            "size": size,
            "pages": result["pages"]
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("cargo.list.error", error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["PUT"])
def update_cargo(cargo_id: str):
    """Update cargo details."""
    data = request.get_json()
    db = get_db()
    
    try:
        cargo_repo = SQLCargoRepository(db)
        cargo = cargo_repo.find_by_id(UUID(cargo_id))
        
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
            
        # Check if cargo can be updated
        if cargo.status == "in_transit":
            return jsonify({"error": "Cannot update cargo in transit"}), 409
            
        # Validate status transition if status is being updated
        if "status" in data and not validate_status_transition(cargo.status, data["status"]):
            return jsonify({"error": "Invalid status transition"}), 400
            
        # Update cargo fields
        update_data = {}
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
                update_data["value"] = str(value)  # Convert Decimal to string for SQLite
            except (TypeError, ValueError, InvalidOperation):
                return jsonify({"error": "Invalid value format"}), 400
                
        if "cargo_type" in data:
            update_data["cargo_type"] = data["cargo_type"]
            
        if "special_requirements" in data:
            update_data["special_requirements"] = data["special_requirements"]
            
        if "status" in data:
            update_data["status"] = data["status"]
        
        # Update the cargo
        cargo_model = cargo_repo.get(str(cargo.id))
        cargo_model.update(**update_data)
        updated_cargo = cargo_repo._to_domain(cargo_model)
        
        # Log cargo update
        log_cargo_operation(
            "update",
            cargo_id,
            {
                "status": updated_cargo.status,
                "updated_fields": list(update_data.keys())
            }
        )
        
        return jsonify(updated_cargo.to_dict()), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        logger.error("cargo.update.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@cargo_bp.route("/<cargo_id>", methods=["DELETE"])
def delete_cargo(cargo_id: str):
    """Delete cargo entry."""
    db = get_db()
    
    try:
        cargo_repo = SQLCargoRepository(db)
        cargo = cargo_repo.find_by_id(UUID(cargo_id))
        
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
            
        # Check if cargo can be deleted
        if cargo.status == "in_transit":
            return jsonify({"error": "Cannot delete cargo in transit"}), 409
            
        # Log cargo deletion
        log_cargo_operation(
            "delete",
            cargo_id,
            {"status": cargo.status}
        )
        
        # Soft delete the cargo
        cargo_repo.soft_delete(str(cargo.id))
        
        return "", 204
        
    except ValueError:
        return jsonify({"error": "Invalid cargo ID format"}), 400
    except Exception as e:
        db.rollback()
        logger.error("cargo.delete.error", cargo_id=cargo_id, error=str(e))
        return jsonify({"error": str(e)}), 500 