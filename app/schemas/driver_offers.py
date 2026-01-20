from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DriverOfferResponse(BaseModel):
    attempt_id: int
    trip_id: int
    driver_id: int

    sent_at: datetime
    responded_at: Optional[datetime]
    response: Optional[str]

    class Config:
        from_attributes = True


class DriverOfferRespondRequest(BaseModel):
    accept: bool
