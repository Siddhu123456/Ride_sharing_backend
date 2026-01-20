from pydantic import BaseModel
from datetime import datetime


class GenerateOtpResponse(BaseModel):
    trip_id: int
    otp_code: str
    expires_at: datetime


class VerifyOtpRequest(BaseModel):
    otp_code: str
