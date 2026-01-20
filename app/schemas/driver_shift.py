from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StartDriverShiftRequest(BaseModel):
    driver_id: int
    tenant_id: int
    latitude: float
    longitude: float


class EndDriverShiftRequest(BaseModel):
    driver_id: int


class DriverShiftResponse(BaseModel):
    shift_id: int
    driver_id: int
    tenant_id: int
    vehicle_id: Optional[int]

    status: str
    started_at: datetime
    ended_at: Optional[datetime]

    expected_end_at: Optional[datetime]

    last_latitude: Optional[float]
    last_longitude: Optional[float]

    class Config:
        from_attributes = True
