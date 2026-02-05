from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.enums import TripStatusEnum, VehicleCategoryEnum


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


class RiderTripHistoryItem(BaseModel):
    trip_id: int
    tenant_id: int
    tenant_name: str

    pickup_address: str
    drop_address: str

    vehicle_category: VehicleCategoryEnum
    fare_amount: float

    status: TripStatusEnum

    created_at: datetime
    completed_at: Optional[datetime] = None


class RiderStatisticsResponse(BaseModel):
    total_rides: int
    total_spent: float
    distance_traveled_km: float