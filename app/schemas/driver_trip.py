from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from app.schemas.enums import TripStatusEnum


class ActiveTripResponse(BaseModel):
    trip_id: int
    status: TripStatusEnum
    pickup_lat: float
    pickup_lng: float
    pickup_address: Optional[str]
    drop_lat: float
    drop_lng: float
    drop_address: Optional[str]
    fare_amount: float | None

    class Config:
        from_attributes = True


class DriverTripItem(BaseModel):
    trip_id: int
    tenant_name: str
    pickup_address: str
    drop_address: str
    fare_amount: float
    status: TripStatusEnum
    completed_at: Optional[datetime]


class DriverTripListResponse(BaseModel):
    page: int
    limit: int
    total: int
    trips: List[DriverTripItem]
