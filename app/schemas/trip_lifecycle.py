from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TripCancelRequest(BaseModel):
    reason: Optional[str] = None


class TripCompleteRequest(BaseModel):
    # for now simple completion (later add distance/time from device)
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None


class TripStatusResponse(BaseModel):
    trip_id: int
    status: str
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None

    requested_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
