from pydantic import BaseModel
from datetime import datetime


class UpdateDriverLocationRequest(BaseModel):
    driver_id: int
    latitude: float
    longitude: float


class DriverLocationResponse(BaseModel):
    driver_id: int
    latitude: float
    longitude: float
    last_updated: datetime

    class Config:
        from_attributes = True
