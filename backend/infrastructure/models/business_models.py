"""SQLAlchemy models for business-related entities."""
import json
from sqlalchemy import Column, String, JSON

from ..database import Base


class BusinessEntityModel(Base):
    """SQLAlchemy model for business entities."""
    __tablename__ = "business_entities"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    certifications = Column(JSON, nullable=False)
    operating_countries = Column(JSON, nullable=False)
    cost_overheads = Column(JSON, nullable=False)  # Stored as JSON string of decimal values

    def get_certifications(self) -> list[str]:
        """Get certifications as list."""
        return json.loads(self.certifications)

    def set_certifications(self, certifications: list[str]):
        """Set certifications from list."""
        self.certifications = json.dumps(certifications)

    def get_operating_countries(self) -> list[str]:
        """Get operating countries as list."""
        return json.loads(self.operating_countries)

    def set_operating_countries(self, countries: list[str]):
        """Set operating countries from list."""
        self.operating_countries = json.dumps(countries)

    def get_cost_overheads(self) -> dict[str, str]:
        """Get cost overheads as dictionary with decimal strings."""
        return json.loads(self.cost_overheads)

    def set_cost_overheads(self, overheads: dict[str, str]):
        """Set cost overheads from dictionary with decimal strings."""
        self.cost_overheads = json.dumps(overheads) 