from pydantic import BaseModel
from app.schemas.enums import VehicleCategoryEnum
from typing import Optional


class TripRequestCreate(BaseModel):
    tenant_id: int
    pickup_lat: float
    pickup_lng: float
    pickup_address: Optional[str]

    drop_lat: float
    drop_lng: float
    drop_address: Optional[str]

    vehicle_category: VehicleCategoryEnum


class TripResponse(BaseModel):
    trip_id: int
    status: str
    fare_amount: float | None

    class Config:
        from_attributes = True
