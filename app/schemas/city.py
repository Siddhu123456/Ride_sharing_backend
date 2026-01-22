from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class CityResponse(BaseModel):
    city_id: int
    country_code: str
    name: str
    timezone: str
    currency: str
    boundary: Optional[Any] = None  # GeoJSON or None
    created_on: datetime

    class Config:
        from_attributes = True


class CityBoundaryUpdateRequest(BaseModel):
    # ✅ frontend will send GeoJSON polygon like:
    # { "type": "Polygon", "coordinates": [[[lng,lat],...]] }
    boundary_geojson: dict
