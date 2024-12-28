"""Cargo and cost-related domain entities for LoadApp.AI."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Cargo(BaseModel):
    """Represents cargo being transported."""
    id: UUID = Field(..., description="Cargo identifier")
    weight: float = Field(..., gt=0, description="Cargo weight in kg")
    value: Decimal = Field(..., gt=0, description="Cargo value")
    special_requirements: List[str] = Field(default_factory=list, description="Special handling requirements")


class CostSettings(BaseModel):
    """Configuration for cost calculations."""
    id: UUID = Field(..., description="Cost settings identifier")
    route_id: UUID = Field(..., description="Reference to route")
    enabled_components: List[str] = Field(..., min_items=1, description="Enabled cost components")
    rates: Dict[str, Decimal] = Field(..., description="Cost rates by component")
    business_entity_id: UUID = Field(..., description="Reference to business entity")


class CostBreakdown(BaseModel):
    """Detailed breakdown of transport costs."""
    route_id: UUID = Field(..., description="Reference to route")
    fuel_costs: Dict[str, Decimal] = Field(..., description="Fuel costs by country")
    toll_costs: Dict[str, Decimal] = Field(..., description="Toll costs by country")
    driver_costs: Decimal = Field(..., ge=0, description="Driver costs")
    overhead_costs: Decimal = Field(..., ge=0, description="Overhead costs")
    timeline_event_costs: Dict[str, Decimal] = Field(..., description="Costs by timeline event")
    total_cost: Decimal = Field(..., ge=0, description="Total transport cost")


class Offer(BaseModel):
    """Represents a transport offer with optional AI enhancement."""
    id: UUID = Field(..., description="Offer identifier")
    route_id: UUID = Field(..., description="Reference to route")
    cost_breakdown_id: UUID = Field(..., description="Reference to cost breakdown")
    margin_percentage: Decimal = Field(..., ge=0, le=100, description="Profit margin percentage")
    final_price: Decimal = Field(..., gt=0, description="Final offer price")
    ai_content: Optional[str] = Field(None, description="AI-generated content")
    fun_fact: Optional[str] = Field(None, description="Fun fact about the transport")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Offer creation timestamp") 