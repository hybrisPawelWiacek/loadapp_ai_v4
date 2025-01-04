"""Initialize default rate validation rules in the database."""
from backend.domain.entities.rate_types import get_default_validation_schemas
from backend.infrastructure.database import SessionLocal
from backend.infrastructure.models.rate_models import RateValidationRuleModel


def init_rate_validation_rules():
    """Initialize default rate validation rules."""
    session = SessionLocal()
    try:
        # Get default schemas
        default_schemas = get_default_validation_schemas()
        
        # Convert and save each schema
        for schema in default_schemas.values():
            model = RateValidationRuleModel.from_domain(schema)
            session.add(model)
        
        session.commit()
        print("Successfully initialized rate validation rules")
        
    except Exception as e:
        print(f"Error initializing rate validation rules: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_rate_validation_rules() 