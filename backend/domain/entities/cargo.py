"""Cargo and cost-related domain entities for LoadApp.AI."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Cargo(BaseModel):
    """Represents cargo being transported."""
    id: UUID = Field(..., description="Cargo identifier")
    business_entity_id: Optional[UUID] = Field(None, description="Reference to business entity")
    weight: float = Field(..., gt=0, description="Cargo weight in kg")
    volume: float = Field(default=0.0, gt=0, description="Cargo volume in cubic meters")
    cargo_type: str = Field(default='general', description="Type of cargo")
    value: Decimal = Field(..., gt=0, description="Cargo value")
    special_requirements: List[str] = Field(default_factory=list, description="Special handling requirements")
    status: str = Field(default='pending', description="Cargo status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the cargo is active")

    def to_dict(self) -> Dict:
        """Convert cargo to dictionary."""
        return {
            "id": str(self.id),
            "business_entity_id": str(self.business_entity_id) if self.business_entity_id else None,
            "weight": self.weight,
            "volume": self.volume,
            "cargo_type": self.cargo_type,
            "value": str(self.value),
            "special_requirements": self.special_requirements,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


class CostSettings(BaseModel):
    """Configuration for cost calculations."""
    id: UUID = Field(..., description="Cost settings identifier")
    route_id: UUID = Field(..., description="Reference to route")
    enabled_components: List[str] = Field(..., min_items=1, description="Enabled cost components")
    rates: Dict[str, Decimal] = Field(..., description="Cost rates by component")
    business_entity_id: UUID = Field(..., description="Reference to business entity")


class CostBreakdown(BaseModel):
    """Detailed breakdown of transport costs."""
    id: UUID = Field(..., description="Cost breakdown identifier")
    route_id: UUID = Field(..., description="Reference to route")
    fuel_costs: Dict[str, Decimal] = Field(default_factory=dict, description="Fuel costs by country")
    toll_costs: Dict[str, Decimal] = Field(default_factory=dict, description="Toll costs by country")
    driver_costs: Decimal = Field(default=Decimal('0'), ge=0, description="Driver costs")
    overhead_costs: Decimal = Field(default=Decimal('0'), ge=0, description="Overhead costs")
    timeline_event_costs: Dict[str, Decimal] = Field(default_factory=dict, description="Costs by timeline event")
    total_cost: Decimal = Field(default=Decimal('0'), ge=0, description="Total transport cost")


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
    status: str = Field(default="draft", description="Offer status (draft, finalized)")

    def to_dict(self) -> Dict:
        """Convert offer to dictionary."""
        return {
            "id": str(self.id),
            "route_id": str(self.route_id),
            "cost_breakdown_id": str(self.cost_breakdown_id),
            "margin_percentage": str(self.margin_percentage),
            "final_price": str(self.final_price),
            "ai_content": self.ai_content,
            "fun_fact": self.fun_fact,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        } 