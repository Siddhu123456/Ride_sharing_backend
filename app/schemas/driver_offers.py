from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DriverOfferResponse(BaseModel):
    attempt_id: int
    trip_id: int

    # 🚕 Trip info
    pickup_lat: float
    pickup_lng: float
    pickup_address: Optional[str]

    drop_lat: float
    drop_lng: float
    drop_address: Optional[str]

    fare_amount: Optional[float]

    # ⏱ Offer info
    sent_at: datetime

    class Config:
        from_attributes = True


class DriverOfferRespondRequest(BaseModel):
    accept: bool
