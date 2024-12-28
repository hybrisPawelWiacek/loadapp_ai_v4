"""Location domain entity."""
from pydantic import BaseModel, Field

class Location(BaseModel):
    """Represents a geographical location with address."""
    
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude coordinate"
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude coordinate"
    )
    address: str = Field(
        default="",
        description="Location address (optional for intermediate points)"
    )

    class Config:
        frozen = True  # Makes the class immutable 