from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GenerateOtpResponse(BaseModel):
    trip_id: int
    otp_code: str
    expires_at: datetime


class VerifyOtpRequest(BaseModel):
    otp_code: str


class TripDriverResponse(BaseModel):
    driver_id: int
    name: str
    phone: str


class TripVehicleResponse(BaseModel):
    vehicle_id: Optional[int]
    registration_no: Optional[str]
    model: Optional[str]
    category: Optional[str]


class TripOtpResponse(BaseModel):
    otp: Optional[str]
    driver: Optional[TripDriverResponse]
    vehicle: Optional[TripVehicleResponse]
