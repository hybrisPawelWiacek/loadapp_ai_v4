"""Business domain entities for LoadApp.AI."""
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class BusinessEntity(BaseModel):
    """Represents a business entity."""
    id: UUID = Field(..., description="Business entity identifier")
    name: str = Field(..., min_length=1, description="Business name")
    address: str = Field(..., description="Business address")
    contact_info: Dict = Field(..., description="Contact information")
    business_type: str = Field(..., description="Type of business")
    certifications: List[str] = Field(..., min_length=1, description="Business certifications")
    operating_countries: List[str] = Field(..., min_length=1, description="Countries of operation")
    cost_overheads: Dict[str, Decimal] = Field(default_factory=dict, description="Cost overhead factors")
    is_active: bool = Field(default=True, description="Business active status")

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate business name."""
        if not v or not v.strip():
            raise ValueError("Business name cannot be empty")
        return v.strip()

    @field_validator('certifications')
    def validate_certifications(cls, v: List[str]) -> List[str]:
        """Validate business certifications."""
        if not v:
            raise ValueError("At least one certification is required")
        return v

    @field_validator('operating_countries')
    def validate_operating_countries(cls, v: List[str]) -> List[str]:
        """Validate operating countries."""
        if not v:
            raise ValueError("At least one operating country is required")
        return v

    @field_validator('cost_overheads')
    def validate_cost_overheads(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate cost overheads."""
        if v is None:
            raise ValueError("Cost overheads cannot be None")
        try:
            return {k: Decimal(str(val)) for k, val in v.items()}
        except (TypeError, ValueError):
            raise ValueError("Cost overhead values must be valid decimal numbers")

    def to_dict(self) -> Dict:
        """Convert business entity to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "address": self.address,
            "contact_info": self.contact_info,
            "business_type": self.business_type,
            "certifications": self.certifications,
            "operating_countries": self.operating_countries,
            "cost_overheads": {k: str(v) for k, v in self.cost_overheads.items()},
            "is_active": self.is_active
        } 