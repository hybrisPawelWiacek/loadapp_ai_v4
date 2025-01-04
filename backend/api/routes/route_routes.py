"""Route-related API routes."""
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4
from flask import Blueprint, jsonify, request, g

from ...domain.entities.location import Location
from ...domain.entities.route import Route, EmptyDriving, TimelineEvent
from ...infrastructure.models.transport_models import TransportModel
from ...infrastructure.models.cargo_models import CargoModel
from ...infrastructure.models.route_models import RouteModel
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

@route_bp.route("/calculate", methods=["POST"])
def calculate_route():
    """Calculate a new route."""
    data = request.get_json()
    _log_route_request(data, "calculate")
    db = g.db
    
    try:
        # Get business entity service
        logger.debug("Getting business service from container")
        business_service = get_container().business_service()
        
        # Validate transport exists
        logger.debug(f"Validating transport: {data.get('transport_id')}")
        transport = db.query(TransportModel).filter_by(id=data["transport_id"]).first()
        if not transport:
            logger.error(f"Transport not found: {data.get('transport_id')}")
            return jsonify({"error": "Transport not found"}), 404
        
        # Validate cargo exists
        logger.debug(f"Validating cargo: {data.get('cargo_id')}")
        cargo = db.query(CargoModel).filter_by(id=data["cargo_id"]).first()
        if not cargo:
            logger.error(f"Cargo not found: {data.get('cargo_id')}")
            return jsonify({"error": "Cargo not found"}), 404
        
        # Parse dates
        try:
            logger.debug("Parsing dates", extra={'pickup': data.get('pickup_time'), 'delivery': data.get('delivery_time')})
            pickup_time = datetime.fromisoformat(data["pickup_time"].replace("Z", "+00:00"))
            delivery_time = datetime.fromisoformat(data["delivery_time"].replace("Z", "+00:00"))
        except (ValueError, KeyError) as e:
            logger.error(f"Date parsing error: {str(e)}", extra={'pickup': data.get('pickup_time'), 'delivery': data.get('delivery_time')})
            return jsonify({"error": f"Invalid date format: {str(e)}"}), 400
        
        # Validate dates
        if delivery_time <= pickup_time:
            logger.error("Invalid dates: delivery time must be after pickup time", 
                        extra={'pickup': pickup_time.isoformat(), 'delivery': delivery_time.isoformat()})
            return jsonify({"error": "Delivery time must be after pickup time"}), 400
        
        # Initialize services
        try:
            logger.debug("Initializing services")
            location_repo = SQLLocationRepository(db)
            google_maps_service = GoogleMapsService(
                api_key="test-key",  # Use test key for now
                location_repo=location_repo
            )
            google_maps_adapter = GoogleMapsAdapter(
                google_maps_service=google_maps_service,
                location_repo=location_repo
            )
            route_service = RouteService(
                route_repo=SQLRouteRepository(db),
                route_calculator=google_maps_adapter,
                location_repo=location_repo
            )
        except Exception as e:
            logger.error("Failed to initialize services", exc_info=True)
            return jsonify({"error": "Service initialization failed"}), 500
        
        # Create route
        try:
            logger.debug("Creating route", extra={
                'transport_id': transport.id,
                'business_entity_id': transport.business_entity_id,
                'cargo_id': cargo.id,
                'origin_id': data["origin_id"],
                'destination_id': data["destination_id"]
            })
            route = route_service.create_route(
                transport_id=UUID(transport.id),
                business_entity_id=UUID(transport.business_entity_id),
                cargo_id=UUID(cargo.id),
                origin_id=UUID(data["origin_id"]),
                destination_id=UUID(data["destination_id"]),
                pickup_time=pickup_time,
                delivery_time=delivery_time
            )
            
            logger.debug("Route created, performing validations")
            validation_timestamp = datetime.now(timezone.utc)
            logger.debug(f"Setting validation timestamp: {validation_timestamp.isoformat()}")
            
            validation_details = {
                "cargo_type": cargo.cargo_type,
                "validation_type": "mock_poc",
                "mock_required_certifications": [],  # Would be populated in production
                "mock_operating_countries": [],  # Would be populated in production
                "route_countries": [],  # Will be populated later
                "validation_timestamp": validation_timestamp.isoformat()
            }
            logger.debug("Initial validation_details structure:", extra={'validation_details': validation_details})
            
            # Mock validation 1: Certifications for cargo type
            logger.debug("Starting certifications validation", extra={
                'cargo_type': cargo.cargo_type,
                'business_entity_id': transport.business_entity_id
            })
            business_service.validate_certifications(
                cargo_type=cargo.cargo_type,
                business_entity_id=UUID(transport.business_entity_id)
            )
            logger.debug("Certifications validation completed successfully")
            
            # Mock validation 2: Operating countries from route segments
            route_countries = {segment.country_code for segment in route.country_segments}
            logger.debug("Starting operating countries validation", extra={
                'route_countries': list(route_countries),
                'business_entity_id': transport.business_entity_id
            })
            business_service.validate_operating_countries(
                business_entity_id=UUID(transport.business_entity_id),
                route_countries=route_countries
            )
            logger.debug("Operating countries validation completed successfully")
            
            # Update validation details
            validation_details.update({
                "route_countries": list(route_countries),
                "validation_timestamp": validation_timestamp.isoformat()
            })
            logger.debug("Updated validation_details:", extra={'validation_details': validation_details})
            
            # Update route with validation results
            logger.debug("Updating route model with validation results", extra={
                'route_id': str(route.id),
                'validation_timestamp': validation_timestamp.isoformat()
            })
            route_model = db.query(RouteModel).filter_by(id=str(route.id)).first()
            if not route_model:
                logger.error(f"Route model not found after creation: {route.id}")
                return jsonify({"error": "Failed to update route with validation results"}), 500
                
            route_model.certifications_validated = True  # Mock result for PoC
            route_model.operating_countries_validated = True  # Mock result for PoC
            route_model.validation_timestamp = validation_timestamp
            route_model.validation_details = validation_details
            logger.debug("Route model updated with validation results", extra={
                'route_id': str(route.id),
                'validation_details': route_model.validation_details,
                'validation_timestamp': route_model.validation_timestamp.isoformat() if route_model.validation_timestamp else None
            })
            
            db.commit()
            logger.debug("Database commit completed")
            
            # Fetch updated route
            logger.debug(f"Fetching updated route with ID: {route_model.id}")
            route = route_service.get_route(UUID(route_model.id))
            if not route:
                logger.error(f"Failed to fetch updated route: {route_model.id}")
                return jsonify({"error": "Failed to fetch updated route"}), 500
            logger.debug("Updated route fetched successfully", extra={
                'route_id': str(route.id),
                'has_validation_details': hasattr(route, 'validation_details'),
                'validation_timestamp': route.validation_timestamp.isoformat() if hasattr(route, 'validation_timestamp') else None
            })
            
            # Log validation results
            logger.info("Route validations complete", extra={
                'route_id': str(route.id),
                'cargo_type': cargo.cargo_type,
                'route_countries': list(route_countries),
                'business_entity_id': str(transport.business_entity_id),
                'validation_details': validation_details
            })
            
        except ValueError as e:
            logger.error(f"Value error creating route: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error("Failed to create route", exc_info=True)
            return jsonify({"error": "Failed to create route"}), 500

        # Convert to response format
        try:
            logger.debug("Converting route to response format")
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
                    "empty_driving_id": str(route.empty_driving_id),
                    "timeline_events": [
                        {
                            "id": str(event.id),
                            "type": event.type,
                            "location": {
                                "id": str(event.location_id),
                                "latitude": location_repo.find_by_id(event.location_id).latitude,
                                "longitude": location_repo.find_by_id(event.location_id).longitude,
                                "address": location_repo.find_by_id(event.location_id).address
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
                            "start_location": {
                                "id": str(segment.start_location_id),
                                "latitude": location_repo.find_by_id(segment.start_location_id).latitude,
                                "longitude": location_repo.find_by_id(segment.start_location_id).longitude,
                                "address": location_repo.find_by_id(segment.start_location_id).address
                            },
                            "end_location": {
                                "id": str(segment.end_location_id),
                                "latitude": location_repo.find_by_id(segment.end_location_id).latitude,
                                "longitude": location_repo.find_by_id(segment.end_location_id).longitude,
                                "address": location_repo.find_by_id(segment.end_location_id).address
                            }
                        }
                        for segment in route.country_segments
                    ],
                    "total_distance_km": route.total_distance_km,
                    "total_duration_hours": route.total_duration_hours,
                    "is_feasible": route.is_feasible,
                    "status": route.status.value,
                    "validations": {
                        "certifications_validated": route_model.certifications_validated,
                        "operating_countries_validated": route_model.operating_countries_validated,
                        "validation_timestamp": route_model.validation_timestamp.isoformat(),
                        "validation_details": route_model.validation_details
                    }
                }
            }
            logger.debug("Route response prepared successfully")
            return jsonify(response), 200
        except Exception as e:
            logger.error("Failed to format response", exc_info=True)
            return jsonify({"error": "Failed to format response"}), 500
            
    except Exception as e:
        logger.error("Unexpected error in calculate_route", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


@route_bp.route("/check-feasibility", methods=["POST"])
def check_route_feasibility():
    """Check route feasibility."""
    data = request.get_json()
    db = g.db
    
    try:
        # Initialize services
        location_repo = SQLLocationRepository(db)
        google_maps_service = GoogleMapsService(
            api_key="test-key",  # Use test key for now
            location_repo=location_repo
        )
        google_maps_adapter = GoogleMapsAdapter(
            google_maps_service=google_maps_service,
            location_repo=location_repo
        )
        route_service = RouteService(
            route_repo=SQLRouteRepository(db),
            route_calculator=google_maps_adapter,
            location_repo=location_repo
        )
        
        # For PoC, always return feasible with some validation details
        response = {
            "is_feasible": True,
            "validation_details": {
                "transport_valid": True,
                "cargo_valid": True,
                "timeline_valid": True,
                "distance_valid": True
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/timeline", methods=["GET"])
def get_route_timeline(route_id):
    """Get route timeline events."""
    db = g.db
    
    try:
        # Initialize repository
        route_repo = SQLRouteRepository(db)
        
        # Get route
        try:
            route = route_repo.find_by_id(UUID(route_id))
            if not route:
                return jsonify({"error": "Route not found"}), 404
        except ValueError as e:
            return jsonify({"error": f"Invalid route ID: {str(e)}"}), 400
            
        # Get timeline events
        events = []
        location_repo = SQLLocationRepository(db)
        for event in route.timeline_events:
            try:
                location = location_repo.find_by_id(event.location_id)
                if not location:
                    logger.error(f"Location not found for event {event.id}")
                    continue
                    
                events.append({
                    "id": str(event.id),
                    "type": event.type,
                    "location": {
                        "id": str(location.id),
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                        "address": location.address
                    },
                    "planned_time": event.planned_time.isoformat(),
                    "duration_hours": event.duration_hours,
                    "event_order": event.event_order
                })
            except Exception as e:
                logger.error(f"Failed to process event {event.id}", exc_info=True)
                continue
                
        return jsonify({"timeline_events": events}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Failed to get route timeline", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/segments", methods=["GET"])
def get_route_segments(route_id):
    """Get route segments."""
    logger.info(f"Getting route segments for route {route_id}")
    db = g.db
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        location_repo = SQLLocationRepository(db)
        
        # Get route
        try:
            route = route_repo.find_by_id(UUID(route_id))
            if not route:
                logger.error(f"Route not found: {route_id}")
                return jsonify({"error": "Route not found"}), 404
        except ValueError:
            return jsonify({"error": "Invalid route ID"}), 400
            
        logger.info(f"Found route {route_id} with {len(route.country_segments) if route.country_segments else 0} segments")
        
        # Convert segments to response format
        segments = []
        for segment in route.country_segments:
            try:
                # Get location details
                start_location = location_repo.find_by_id(segment.start_location_id)
                end_location = location_repo.find_by_id(segment.end_location_id)
                
                if not start_location or not end_location:
                    logger.error(f"Location not found for segment - start: {segment.start_location_id}, end: {segment.end_location_id}")
                    continue
                
                logger.debug(f"Processing segment - country: {segment.country_code}, distance: {segment.distance_km}km, " +
                           f"duration: {segment.duration_hours}h, start: {segment.start_location_id}, end: {segment.end_location_id}")
                
                segments.append({
                    "country_code": segment.country_code,
                    "distance_km": segment.distance_km,
                    "duration_hours": segment.duration_hours,
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
                    }
                })
            except Exception as e:
                logger.error(f"Failed to process segment: {str(e)}")
                continue
        
        logger.info(f"Returning {len(segments)} segments for route {route_id}")
        
        return jsonify({"segments": segments}), 200
        
    except Exception as e:
        logger.error(f"Error getting route segments for route {route_id}: {str(e)} ({type(e).__name__})")
        return jsonify({"error": "Failed to get route segments"}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/timeline", methods=["PUT"])
def update_route_timeline(route_id):
    """Update route timeline events."""
    data = request.get_json()
    db = g.db
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        location_repo = SQLLocationRepository(db)
        
        # Get route
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
            
        # Validate timeline events
        events = []
        for event_data in data["timeline_events"]:
            try:
                # Validate location exists
                location = location_repo.find_by_id(UUID(event_data["location_id"]))
                if not location:
                    return jsonify({"error": f"Location not found: {event_data['location_id']}"}), 400
                    
                # Parse planned time
                planned_time = datetime.fromisoformat(event_data["planned_time"].replace("Z", "+00:00"))
                
                # Create event
                event = TimelineEvent(
                    id=uuid4(),
                    route_id=route.id,
                    type=event_data["type"],
                    location_id=location.id,
                    planned_time=planned_time,
                    duration_hours=float(event_data["duration_hours"]),
                    event_order=int(event_data["event_order"])
                )
                events.append(event)
                
            except (ValueError, KeyError) as e:
                return jsonify({"error": f"Invalid event data: {str(e)}"}), 400
                
        # Validate event sequence
        events.sort(key=lambda x: x.event_order)
        
        # Check event types
        if len(events) > 0:
            if events[0].type != "pickup":
                return jsonify({"error": "Invalid event sequence: first event must be pickup"}), 400
            if len(events) > 1 and events[-1].type != "delivery":
                return jsonify({"error": "Invalid event sequence: last event must be delivery"}), 400
        
        # Check chronological order
        for i in range(len(events) - 1):
            if events[i].planned_time >= events[i + 1].planned_time:
                return jsonify({"error": "Invalid event sequence: events must be in chronological order"}), 400
                
        # Update route timeline
        route.timeline_events = events
        updated_route = route_repo.save(route)
        
        # Return updated timeline
        response_events = []
        for event in updated_route.timeline_events:
            location = location_repo.find_by_id(event.location_id)
            response_events.append({
                "id": str(event.id),
                "type": event.type,
                "location": {
                    "id": str(location.id),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "address": location.address
                },
                "planned_time": event.planned_time.isoformat(),
                "duration_hours": event.duration_hours,
                "event_order": event.event_order
            })
            
        return jsonify({"timeline_events": response_events}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Failed to update route timeline", error=str(e))
        return jsonify({"error": "Internal server error"}), 500 