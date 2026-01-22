from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ZoneResponse(BaseModel):
    zone_id: int
    city_id: int
    name: str
    boundary: Optional[Any] = None
    created_on: datetime

    class Config:
        from_attributes = True


class ZoneBoundaryUpdateRequest(BaseModel):
    boundary_geojson: dict
