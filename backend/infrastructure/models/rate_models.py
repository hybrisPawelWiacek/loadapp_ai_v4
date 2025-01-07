"""SQLAlchemy models for rate validation rules."""
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Column, String, Numeric, Boolean
from sqlalchemy.sql import text

from ..database import Base
from ...domain.entities.rate_types import RateType, RateValidationSchema


class RateValidationRuleModel(Base):
    """SQLAlchemy model for rate validation rules."""
    __tablename__ = 'rate_validation_rules'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rate_type = Column(String(50), nullable=False, index=True)
    min_value = Column(Numeric(10, 2), nullable=False)
    max_value = Column(Numeric(10, 2), nullable=False)
    country_specific = Column(Boolean, nullable=False, server_default=text('0'))
    requires_certification = Column(Boolean, nullable=False, server_default=text('0'))
    description = Column(String(200))

    @classmethod
    def from_domain(cls, schema: RateValidationSchema) -> 'RateValidationRuleModel':
        """Create model instance from domain entity."""
        return cls(
            id=str(uuid4()),
            rate_type=schema.rate_type.value,
            min_value=schema.min_value,
            max_value=schema.max_value,
            country_specific=schema.country_specific,
            requires_certification=schema.requires_certification,
            description=schema.description
        )

    def to_domain(self) -> RateValidationSchema:
        """Convert to domain entity."""
        return RateValidationSchema(
            rate_type=RateType(self.rate_type),
            min_value=Decimal(str(self.min_value)),
            max_value=Decimal(str(self.max_value)),
            country_specific=bool(self.country_specific),
            requires_certification=bool(self.requires_certification),
            description=self.description
        ) 