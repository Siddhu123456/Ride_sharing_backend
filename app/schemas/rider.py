from datetime import datetime
from pydantic import BaseModel


class RiderProfileResponse(BaseModel):
    user_id: int
    full_name: str
    phone: str
    email: str
    gender: str
    country_code: str
    status: str
    joined_on: datetime

    class Config:
        from_attributes = True


class RiderCityResponse(BaseModel):
    city_id: int
    city_name: str
    country_code: str
