from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.enums import VehicleCategoryEnum, TripStatusEnum


class TripRequestCreate(BaseModel):
    tenant_id: int
    city_id: int  # ✅ for now we take city_id directly (later GPS->city mapping)
    pickup_lat: float
    pickup_lng: float
    drop_lat: Optional[float] = None
    drop_lng: Optional[float] = None
    vehicle_category: VehicleCategoryEnum


class TripResponse(BaseModel):
    trip_id: int
    tenant_id: int
    rider_id: int
    driver_id: Optional[int]
    vehicle_id: Optional[int]

    city_id: int
    zone_id: Optional[int]

    pickup_lat: float
    pickup_lng: float
    drop_lat: Optional[float]
    drop_lng: Optional[float]

    vehicle_category: VehicleCategoryEnum
    status: TripStatusEnum

    requested_at: datetime
    assigned_at: Optional[datetime]

    class Config:
        from_attributes = True
