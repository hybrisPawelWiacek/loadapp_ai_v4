"""Business domain entities for LoadApp.AI."""
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessEntity(BaseModel):
    """Represents a transport company."""
    id: UUID = Field(..., description="Business entity identifier")
    name: str = Field(..., min_length=1, description="Company name")
    certifications: List[str] = Field(..., min_items=1, description="Company certifications")
    operating_countries: List[str] = Field(..., min_items=1, description="Countries where company operates")
    cost_overheads: Dict[str, Decimal] = Field(..., description="Overhead costs by category") 