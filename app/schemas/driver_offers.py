from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class DriverOfferResponse(BaseModel):
    attempt_id: int
    trip_id: int

    pickup_lat: float
    pickup_lng: float
    pickup_address: str

    drop_lat: float
    drop_lng: float
    drop_address: str

    distance_km: float   # Distance in kilometers (new field)
    fare_amount: float

    sent_at: datetime

    class Config:
        from_attributes = True


class DriverOfferRespondRequest(BaseModel):
    accept: bool
