"""Route domain entities."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .location import Location


class RouteStatus(str, Enum):
    """Route status enumeration."""
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventStatus(str, Enum):
    """Timeline event status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmptyDriving(BaseModel):
    """Empty driving segment before main route."""
    
    id: UUID = Field(
        ...,
        description="Empty driving segment identifier"
    )
    distance_km: float = Field(
        default=200.0,
        gt=0,
        description="Empty driving distance in kilometers"
    )
    duration_hours: float = Field(
        default=4.0,
        gt=0,
        description="Empty driving duration in hours"
    )


class RouteSegment(BaseModel):
    """Segment of a route with distance and duration."""
    
    distance_km: float = Field(
        ...,
        gt=0,
        description="Segment distance in kilometers"
    )
    duration_hours: float = Field(
        ...,
        gt=0,
        description="Segment duration in hours"
    )
    start_location_id: UUID = Field(
        ...,
        description="Start location ID"
    )
    end_location_id: UUID = Field(
        ...,
        description="End location ID"
    )


class CountrySegment(BaseModel):
    """Route segment within a single country."""
    
    id: UUID = Field(
        ...,
        description="Country segment identifier"
    )
    route_id: Optional[UUID] = Field(
        default=None,
        description="Reference to route"
    )
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code"
    )
    distance_km: float = Field(
        ...,
        gt=0,
        description="Distance within country in kilometers"
    )
    duration_hours: float = Field(
        ...,
        gt=0,
        description="Duration within country in hours"
    )
    start_location_id: UUID = Field(
        ...,
        description="Start location ID"
    )
    end_location_id: UUID = Field(
        ...,
        description="End location ID"
    )
    segment_order: int = Field(
        ...,
        ge=0,
        description="Order of segment in route"
    )


class TimelineEvent(BaseModel):
    """Event in route timeline (pickup/rest/delivery)."""
    
    id: UUID = Field(
        ...,
        description="Event identifier"
    )
    route_id: UUID = Field(
        ...,
        description="Reference to route"
    )
    type: str = Field(
        ...,
        min_length=1,
        description="Event type (pickup/rest/delivery)"
    )
    location_id: UUID = Field(
        ...,
        description="Event location ID"
    )
    planned_time: datetime = Field(
        ...,
        description="Planned event time"
    )
    duration_hours: float = Field(
        default=1.0,
        gt=0,
        description="Event duration in hours"
    )
    event_order: int = Field(
        ...,
        ge=0,
        description="Order of event in timeline"
    )
    status: EventStatus = Field(
        default=EventStatus.PENDING,
        description="Event status"
    )
    actual_time: Optional[datetime] = Field(
        default=None,
        description="Actual time when event occurred"
    )

    def to_dict(self) -> dict:
        """Convert timeline event to dictionary."""
        return {
            'id': str(self.id),
            'route_id': str(self.route_id),
            'type': self.type,
            'location_id': str(self.location_id),
            'planned_time': self.planned_time.isoformat() if self.planned_time else None,
            'duration_hours': self.duration_hours,
            'event_order': self.event_order,
            'status': self.status.value,
            'actual_time': self.actual_time.isoformat() if self.actual_time else None
        }


class Route(BaseModel):
    """Complete transport route with timeline."""
    
    id: UUID = Field(
        ...,
        description="Route identifier"
    )
    transport_id: UUID = Field(
        ...,
        description="Reference to transport"
    )
    business_entity_id: UUID = Field(
        ...,
        description="Reference to business entity"
    )
    cargo_id: Optional[UUID] = Field(
        default=None,
        description="Reference to cargo"
    )
    origin_id: UUID = Field(
        ...,
        description="Reference to origin location"
    )
    destination_id: UUID = Field(
        ...,
        description="Reference to destination location"
    )
    pickup_time: datetime = Field(
        ...,
        description="Pickup time"
    )
    delivery_time: datetime = Field(
        ...,
        description="Delivery time"
    )
    empty_driving_id: Optional[UUID] = Field(
        default=None,
        description="Reference to empty driving segment"
    )
    timeline_events: List[TimelineEvent] = Field(
        default_factory=list,
        description="Timeline events"
    )
    country_segments: List[CountrySegment] = Field(
        default_factory=list,
        description="Country segments"
    )
    total_distance_km: float = Field(
        ...,
        ge=0,
        description="Total distance in kilometers"
    )
    total_duration_hours: float = Field(
        ...,
        ge=0,
        description="Total duration in hours"
    )
    is_feasible: bool = Field(
        default=True,
        description="Route feasibility flag"
    )
    status: RouteStatus = Field(
        default=RouteStatus.DRAFT,
        description="Route status"
    )
    certifications_validated: bool = Field(
        default=False,
        description="Flag indicating if certifications are validated"
    )
    operating_countries_validated: bool = Field(
        default=False,
        description="Flag indicating if operating countries are validated"
    )
    validation_timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last validation"
    )
    validation_details: dict = Field(
        default_factory=dict,
        description="Additional validation details"
    ) 