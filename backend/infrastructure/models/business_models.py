"""SQLAlchemy models for business-related entities."""
import json
from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class BusinessEntityModel(Base):
    """SQLAlchemy model for business entities."""
    __tablename__ = "business_entities"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    contact_info = Column(JSON, nullable=False)
    business_type = Column(String(50), nullable=False)
    certifications = Column(JSON, nullable=False)
    operating_countries = Column(JSON, nullable=False)
    cost_overheads = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships with deferred loading
    cargos = relationship("CargoModel", back_populates="business_entity", lazy="dynamic", post_update=True)
    transports = relationship("TransportModel", back_populates="business_entity", lazy="dynamic", post_update=True)

    def __init__(self, id, name, address, contact_info, business_type, certifications=None,
                 operating_countries=None, cost_overheads=None, is_active=True):
        self.id = id
        self.name = name
        self.address = address
        self.contact_info = json.dumps(contact_info) if contact_info else "{}"
        self.business_type = business_type
        if isinstance(certifications, str):
            self.certifications = certifications
        else:
            self.certifications = json.dumps(certifications) if certifications else "[]"
        if isinstance(operating_countries, str):
            self.operating_countries = operating_countries
        else:
            self.operating_countries = json.dumps(operating_countries) if operating_countries else "[]"
        if isinstance(cost_overheads, str):
            self.cost_overheads = cost_overheads
        else:
            self.cost_overheads = json.dumps(cost_overheads) if cost_overheads else "{}"
        self.is_active = is_active

    def get_contact_info(self) -> dict:
        """Get contact info as dict."""
        return json.loads(self.contact_info)

    def set_contact_info(self, contact_info: dict):
        """Set contact info from dict."""
        self.contact_info = json.dumps(contact_info) if contact_info else "{}"

    def get_certifications(self) -> list:
        """Get certifications as list."""
        return json.loads(self.certifications)

    def set_certifications(self, certifications: list):
        """Set certifications from list."""
        self.certifications = json.dumps(certifications) if certifications else "[]"

    def get_operating_countries(self) -> list:
        """Get operating countries as list."""
        return json.loads(self.operating_countries)

    def set_operating_countries(self, countries: list):
        """Set operating countries from list."""
        self.operating_countries = json.dumps(countries) if countries else "[]"

    def get_cost_overheads(self) -> dict:
        """Get cost overheads as dict."""
        return json.loads(self.cost_overheads)

    def set_cost_overheads(self, overheads: dict):
        """Set cost overheads from dict."""
        self.cost_overheads = json.dumps(overheads) if overheads else "{}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'contact_info': self.get_contact_info(),
            'business_type': self.business_type,
            'certifications': self.get_certifications(),
            'operating_countries': self.get_operating_countries(),
            'cost_overheads': self.get_cost_overheads()
        } 