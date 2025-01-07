"""Repository for rate validation rules."""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ...domain.entities.rate_types import RateType, RateValidationSchema
from ..models.rate_models import RateValidationRuleModel
from .base import BaseRepository


class RateValidationRepository(BaseRepository[RateValidationRuleModel]):
    """Repository for managing rate validation rules."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        super().__init__(RateValidationRuleModel, db)

    def get_all_schemas(self) -> Dict[RateType, RateValidationSchema]:
        """
        Get all validation schemas.
        
        Returns:
            Dictionary mapping rate types to their validation schemas
        """
        # First try to get schemas from database
        rules = self._db.query(RateValidationRuleModel).all()
        if rules:
            return {RateType(rule.rate_type): rule.to_domain() for rule in rules}
        
        # If no rules in database, generate default schemas from rate types
        return {
            rate_type: RateValidationSchema.from_rate_type(rate_type)
            for rate_type in RateType
        }

    def get_schema(self, rate_type: RateType) -> Optional[RateValidationSchema]:
        """
        Get validation schema for specific rate type.
        
        Args:
            rate_type: Type of rate to get schema for
            
        Returns:
            Validation schema if found, None otherwise
        """
        # First try to get from database
        rule = self._db.query(RateValidationRuleModel).filter(
            RateValidationRuleModel.rate_type == rate_type.value
        ).first()
        
        if rule:
            return rule.to_domain()
        
        # If not in database, generate default schema
        return RateValidationSchema.from_rate_type(rate_type)

    def save_schema(self, schema: RateValidationSchema) -> RateValidationSchema:
        """
        Save validation schema.
        
        Args:
            schema: Schema to save
            
        Returns:
            Saved schema
        """
        # Check if schema already exists
        existing = self._db.query(RateValidationRuleModel).filter(
            RateValidationRuleModel.rate_type == schema.rate_type.value
        ).first()

        if existing:
            # Update existing
            existing.min_value = schema.min_value
            existing.max_value = schema.max_value
            existing.country_specific = schema.country_specific
            existing.requires_certification = schema.requires_certification
            existing.description = schema.description
            model = existing
        else:
            # Create new
            model = RateValidationRuleModel.from_domain(schema)
            self._db.add(model)

        self._db.commit()
        return model.to_domain()

    def save_schemas(self, schemas: List[RateValidationSchema]) -> List[RateValidationSchema]:
        """
        Save multiple validation schemas.
        
        Args:
            schemas: List of schemas to save
            
        Returns:
            List of saved schemas
        """
        return [self.save_schema(schema) for schema in schemas] 