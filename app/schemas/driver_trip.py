from pydantic import BaseModel
from typing import Optional
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
