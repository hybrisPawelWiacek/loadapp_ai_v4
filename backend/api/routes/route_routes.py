"""Route-related API routes."""
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4
from flask import Blueprint, jsonify, request, g

from ...domain.entities.location import Location
from ...domain.entities.route import Route, EmptyDriving, TimelineEvent, SegmentType
from ...infrastructure.models.transport_models import TransportModel
from ...infrastructure.models.cargo_models import CargoModel
from ...infrastructure.models.route_models import (
    RouteModel, RouteStatusHistoryModel, LocationModel,
    EmptyDrivingModel, TimelineEventModel, CountrySegmentModel
)
from ...infrastructure.repositories.route_repository import SQLRouteRepository
from ...infrastructure.repositories.location_repository import SQLLocationRepository
from ...domain.services.route_service import RouteService
from ...infrastructure.adapters.google_maps_adapter import GoogleMapsAdapter
from ...infrastructure.external_services.google_maps_service import GoogleMapsService
from ...infrastructure.container import get_container

logger = logging.getLogger(__name__)

# Create blueprint
route_bp = Blueprint("route", __name__, url_prefix="/api/route")

def _log_route_request(data: dict, endpoint: str) -> None:
    """Log route request details."""
    logger.debug(f"Route {endpoint} request", extra={
        'request_data': data,
        'endpoint': endpoint,
        'method': request.method,
        'content_type': request.content_type
    })

def _log_route_response(route: Route, status: int) -> None:
    """Log route response details."""
    logger.debug("Route operation response", extra={
        'route_id': str(route.id) if route else None,
        'status_code': status,
        'timeline_events': len(route.timeline_events) if route and hasattr(route, 'timeline_events') else 0,
        'country_segments': len(route.country_segments) if route and hasattr(route, 'country_segments') else 0
    })

def _log_timeline_operation(operation: str, events: list, route_id: UUID) -> None:
    """Log timeline operation details."""
    logger.debug(f"Timeline {operation}",
        route_id=str(route_id),
        event_count=len(events),
        event_types=[e.type for e in events] if events else [],
        event_locations=[str(e.location_id) for e in events] if events else []
    )

def _format_distance(distance_km: float) -> str:
    """Format distance in kilometers to a user-friendly string."""
    return f"{round(distance_km, 1)} km"

def _format_duration(duration_hours: float) -> str:
    """Convert decimal hours to a user-friendly hours and minutes format."""
    total_minutes = int(duration_hours * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours == 0:
        return f"{minutes}min"
    return f"{hours}h {minutes}min"

@route_bp.route("/calculate", methods=["POST"])
def calculate_route():
    """Calculate a new route."""
    data = request.get_json()
    _log_route_request(data, "calculate")
    db = g.db
    
    try:
        # Get container
        container = get_container()
        
        # Get services from container
        logger.debug("Getting services from container")
        route_service = container.route_service()
        
        # Parse dates
        try:
            logger.debug("Parsing dates", extra={'pickup': data.get('pickup_time'), 'delivery': data.get('delivery_time')})
            pickup_time = datetime.fromisoformat(data["pickup_time"].replace("Z", "+00:00"))
            delivery_time = datetime.fromisoformat(data["delivery_time"].replace("Z", "+00:00"))
        except (ValueError, KeyError) as e:
            logger.error(f"Date parsing error: {str(e)}", extra={'pickup': data.get('pickup_time'), 'delivery': data.get('delivery_time')})
            return jsonify({"error": f"Invalid date format: {str(e)}"}), 400

        # Validate route creation parameters
        is_valid, error_msg = route_service.validate_route_creation(
            transport_id=UUID(data["transport_id"]),
            cargo_id=UUID(data["cargo_id"]),
            pickup_time=pickup_time,
            delivery_time=delivery_time
        )
        if not is_valid:
            logger.error("Route validation failed", error=error_msg)
            return jsonify({"error": error_msg}), 400

        # Validate truck_location_id is provided
        if "truck_location_id" not in data:
            logger.error("truck_location_id is required")
            return jsonify({"error": "truck_location_id is required"}), 400
            
        # Create route
        try:
            logger.debug("Creating route", extra={
                'transport_id': data["transport_id"],
                'cargo_id': data["cargo_id"],
                'origin_id': data["origin_id"],
                'destination_id': data["destination_id"],
                'truck_location_id': data["truck_location_id"]
            })
            route = route_service.create_route(
                transport_id=UUID(data["transport_id"]),
                business_entity_id=UUID(data["business_entity_id"]),
                cargo_id=UUID(data["cargo_id"]),
                origin_id=UUID(data["origin_id"]),
                destination_id=UUID(data["destination_id"]),
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                truck_location_id=UUID(data["truck_location_id"])
            )
            
            # Check route feasibility
            validation_details = route_service.validate_route_feasibility({
                "transport_id": str(route.transport_id),
                "cargo_id": str(route.cargo_id),
                "origin_id": str(route.origin_id),
                "destination_id": str(route.destination_id),
                "pickup_time": route.pickup_time.isoformat(),
                "delivery_time": route.delivery_time.isoformat()
            })
            
            # Convert to response format
            response = {
                "route": {
                    "id": str(route.id),
                    "transport_id": str(route.transport_id),
                    "cargo_id": str(route.cargo_id),
                    "business_entity_id": str(route.business_entity_id),
                    "origin_id": str(route.origin_id),
                    "destination_id": str(route.destination_id),
                    "pickup_time": route.pickup_time.isoformat(),
                    "delivery_time": route.delivery_time.isoformat(),
                    "empty_driving": {
                        "id": str(route.empty_driving_id),
                        "distance_km": route.empty_driving.distance_km,
                        "duration_hours": route.empty_driving.duration_hours,
                        "route_points": route.empty_driving.route_points if hasattr(route.empty_driving, 'route_points') else None,
                        "start_location": {
                            "id": str(container.location_repository().find_by_id(route.truck_location_id).id),
                            "latitude": container.location_repository().find_by_id(route.truck_location_id).latitude,
                            "longitude": container.location_repository().find_by_id(route.truck_location_id).longitude,
                            "address": container.location_repository().find_by_id(route.truck_location_id).address
                        },
                        "end_location": {
                            "id": str(container.location_repository().find_by_id(route.origin_id).id),
                            "latitude": container.location_repository().find_by_id(route.origin_id).latitude,
                            "longitude": container.location_repository().find_by_id(route.origin_id).longitude,
                            "address": container.location_repository().find_by_id(route.origin_id).address
                        }
                    },
                    "timeline_events": [
                        {
                            "id": str(event.id),
                            "type": event.type,
                            "location": {
                                "id": str(event.location_id),
                                "latitude": container.location_repository().find_by_id(event.location_id).latitude,
                                "longitude": container.location_repository().find_by_id(event.location_id).longitude,
                                "address": container.location_repository().find_by_id(event.location_id).address
                            },
                            "planned_time": event.planned_time.isoformat(),
                            "duration_hours": event.duration_hours,
                            "event_order": event.event_order
                        }
                        for event in route.timeline_events
                    ],
                    "country_segments": [
                        {
                            "country_code": segment.country_code,
                            "distance_km": segment.distance_km,
                            "duration_hours": segment.duration_hours,
                            "route_points": segment.route_points if hasattr(segment, 'route_points') else None,
                            "start_location": {
                                "id": str(segment.start_location_id),
                                "latitude": container.location_repository().find_by_id(segment.start_location_id).latitude,
                                "longitude": container.location_repository().find_by_id(segment.start_location_id).longitude,
                                "address": container.location_repository().find_by_id(segment.start_location_id).address
                            },
                            "end_location": {
                                "id": str(segment.end_location_id),
                                "latitude": container.location_repository().find_by_id(segment.end_location_id).latitude,
                                "longitude": container.location_repository().find_by_id(segment.end_location_id).longitude,
                                "address": container.location_repository().find_by_id(segment.end_location_id).address
                            }
                        }
                        for segment in route.country_segments
                        if segment.segment_type != SegmentType.EMPTY_DRIVING  # Filter out empty driving segments
                    ],
                    "route_polyline": route.route_polyline,
                    "total_distance_km": route.total_distance_km,
                    "total_duration_hours": route.total_duration_hours,
                    "is_feasible": route.is_feasible,
                    "status": route.status.value,
                    "validations": validation_details
                }
            }
            logger.debug("Route response prepared successfully")
            return jsonify(response), 200
            
        except ValueError as e:
            logger.error(f"Value error creating route: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error("Failed to create route", exc_info=True)
            return jsonify({"error": "Failed to create route"}), 500

    except Exception as e:
        logger.error("Unexpected error in calculate_route", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


@route_bp.route("/check-feasibility", methods=["POST"])
def check_route_feasibility():
    """Check route feasibility."""
    data = request.get_json()
    _log_route_request(data, "check-feasibility")
    db = g.db
    
    try:
        # Get services from container
        container = get_container()
        route_service = container.route_service()
        
        # Validate route feasibility
        validation_details = route_service.validate_route_feasibility(data)
        
        response = {
            "is_feasible": all(validation_details.values()),
            "validation_details": validation_details
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error("Validation error in check_route_feasibility", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error in check_route_feasibility", error=str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/timeline", methods=["GET"])
def get_route_timeline(route_id):
    """Get route timeline events."""
    db = g.db
    
    try:
        # Get services from container
        container = get_container()
        route_service = container.route_service()
        location_repo = container.location_repository()
        
        # Get route
        try:
            route = route_service.get_route(UUID(route_id))
            if not route:
                return jsonify({"error": "Route not found"}), 404
        except ValueError as e:
            return jsonify({"error": f"Invalid route ID: {str(e)}"}), 400
            
        # Get timeline events
        events = []
        for event in route.timeline_events:
            try:
                location = location_repo.find_by_id(event.location_id)
                if not location:
                    logger.error(f"Location not found for event {event.id}")
                    continue
                    
                event_dict = event.to_dict()
                event_dict['location'] = {
                    "id": str(location.id),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "address": location.address
                }
                events.append(event_dict)
            except Exception as e:
                logger.error(f"Failed to process event {event.id}", exc_info=True)
                continue
                
        return jsonify({"timeline_events": events}), 200

    except Exception as e:
        logger.error("Failed to get route timeline", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@route_bp.route("/<route_id>/segments", methods=["GET"])
def get_route_segments(route_id):
    """Get route segments for visualization."""
    db = g.db
    
    try:
        # Get services from container
        container = get_container()
        route_service = container.route_service()
        location_repo = container.location_repository()
        maps_service = container.google_maps_service()
        
        # Get route segments
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
            
        segments = []
        
        # Add empty driving if exists
        if route.empty_driving:
            try:
                # Get location details
                start_location = location_repo.find_by_id(route.truck_location_id)
                end_location = location_repo.find_by_id(route.origin_id)
                
                if not start_location or not end_location:
                    logger.error(f"Location not found for empty driving - start: {route.truck_location_id}, end: {route.origin_id}")
                else:
                    # Get route points for empty driving
                    route_points = maps_service.get_segment_route_points(start_location, end_location)
                    
                    empty_dict = {
                        "type": "empty_driving",
                        "distance_km": route.empty_driving.distance_km,
                        "duration_hours": route.empty_driving.duration_hours,
                        "distance_formatted": _format_distance(route.empty_driving.distance_km),
                        "duration_formatted": _format_duration(route.empty_driving.duration_hours),
                        "start_location": {
                            "id": str(start_location.id),
                            "latitude": start_location.latitude,
                            "longitude": start_location.longitude,
                            "address": start_location.address
                        },
                        "end_location": {
                            "id": str(end_location.id),
                            "latitude": end_location.latitude,
                            "longitude": end_location.longitude,
                            "address": end_location.address
                        },
                        "route_points": route_points
                    }
                    segments.append(empty_dict)
                    
                    logger.debug("Added empty driving segment", extra={
                        'start_location': str(empty_dict['start_location']),
                        'end_location': str(empty_dict['end_location']),
                        'route_points_count': len(route_points) if route_points else 0,
                        'route_points_sample': str(route_points[:2]) if route_points else None
                    })
            except Exception as e:
                logger.error(f"Error processing empty driving segment: {str(e)}")
        
        # Add country segments
        for segment in route.country_segments:
            try:
                # Get location details
                start_location = location_repo.find_by_id(segment.start_location_id)
                end_location = location_repo.find_by_id(segment.end_location_id)
                
                if not start_location or not end_location:
                    logger.error(f"Location not found for segment - start: {segment.start_location_id}, end: {segment.end_location_id}")
                    continue
                
                # Get route points for country segment
                route_points = maps_service.get_segment_route_points(start_location, end_location)
                
                segment_dict = {
                    "type": "country",
                    "country_code": segment.country_code,
                    "distance_km": segment.distance_km,
                    "duration_hours": segment.duration_hours,
                    "distance_formatted": _format_distance(segment.distance_km),
                    "duration_formatted": _format_duration(segment.duration_hours),
                    "start_location": {
                        "id": str(start_location.id),
                        "latitude": start_location.latitude,
                        "longitude": start_location.longitude,
                        "address": start_location.address
                    },
                    "end_location": {
                        "id": str(end_location.id),
                        "latitude": end_location.latitude,
                        "longitude": end_location.longitude,
                        "address": end_location.address
                    },
                    "route_points": route_points
                }
                segments.append(segment_dict)
                
                logger.debug("Added country segment", extra={
                    'country_code': segment_dict['country_code'],
                    'start_location': str(segment_dict['start_location']),
                    'end_location': str(segment_dict['end_location']),
                    'route_points_count': len(route_points) if route_points else 0,
                    'route_points_sample': str(route_points[:2]) if route_points else None
                })
            except Exception as e:
                logger.error(f"Error processing country segment: {str(e)}")
                continue
        
        logger.debug("Route segments response prepared", extra={
            'segments_count': len(segments),
            'has_empty_driving': any(s['type'] == 'empty_driving' for s in segments),
            'country_codes': [s['country_code'] for s in segments if s.get('country_code')]
        })
        
        return jsonify({"segments": segments}), 200
        
    except Exception as e:
        logger.error("Failed to get route segments", exc_info=True)
        return jsonify({"error": "Failed to get route segments"}), 500
    finally:
        if 'db' in locals():
            db.close()


@route_bp.route("/<route_id>/timeline", methods=["PUT"])
def update_route_timeline(route_id):
    """Update route timeline events."""
    data = request.get_json()
    _log_route_request(data, "update_timeline")
    db = g.db
    
    try:
        # Get services from container
        container = get_container()
        route_service = container.route_service()
        
        # Get route
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
            
        # Validate timeline events
        is_valid, error_msg, validated_events = route_service.validate_timeline_events(
            events=data["timeline_events"],
            route_id=UUID(route_id)
        )
        if not is_valid:
            logger.error("Timeline validation failed", error=error_msg)
            return jsonify({"error": error_msg}), 400
            
        # Update route timeline
        route.timeline_events = validated_events
        updated_route = route_service.update_route(route)
        
        # Return updated timeline
        response = {
            "timeline_events": [
                {
                    "id": str(event.id),
                    "type": event.type,
                    "location": {
                        "id": str(event.location_id),
                        "latitude": container.location_repository().find_by_id(event.location_id).latitude,
                        "longitude": container.location_repository().find_by_id(event.location_id).longitude,
                        "address": container.location_repository().find_by_id(event.location_id).address
                    },
                    "planned_time": event.planned_time.isoformat(),
                    "duration_hours": event.duration_hours,
                    "event_order": event.event_order
                }
                for event in updated_route.timeline_events
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error("Validation error in update_route_timeline", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error in update_route_timeline", error=str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/status-history", methods=["GET"])
def get_route_status_history(route_id: str):
    """Get route status history."""
    db = g.db
    
    try:
        # Get container
        container = get_container()
        route_repo = container.route_repository()
        
        # Get route
        try:
            route = route_repo.find_by_id(UUID(route_id))
            if not route:
                return jsonify({"error": "Route not found"}), 404
        except ValueError as e:
            return jsonify({"error": f"Invalid route ID: {str(e)}"}), 400
            
        # Get status history
        status_history = route_repo.get_status_history(UUID(route_id))
        
        # Return response
        response = {
            "status_history": [
                {
                    "id": str(history.id),
                    "status": history.status,
                    "comment": history.comment,
                    "timestamp": history.timestamp.isoformat()
                }
                for history in status_history
            ]
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error getting route status history: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to get route status history"}), 500


@route_bp.route("/<route_id>/status", methods=["PUT"])
def update_route_status(route_id: str):
    """Update route status."""
    data = request.get_json()
    _log_route_request(data, "update_status")
    db = g.db
    
    try:
        # Get container
        container = get_container()
        route_service = container.route_service()
        
        # Validate required fields
        if "status" not in data:
            return jsonify({"error": "Status is required"}), 400
            
        # Update status
        success, error_msg, updated_route = route_service.update_route_status(
            route_id=UUID(route_id),
            new_status=data["status"],
            comment=data.get("comment")
        )
        
        if not success:
            return jsonify({"error": error_msg}), 400
            
        return jsonify({
            "message": "Route status updated successfully",
            "old_status": updated_route.status.value,
            "new_status": data["status"]
        }), 200
        
    except ValueError as e:
        logger.error("Validation error in update_route_status", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error in update_route_status", error=str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 