from pydantic import BaseModel
from app.schemas.enums import VehicleCategoryEnum
from typing import Optional, List



class TripRequestCreate(BaseModel):
    tenant_id: int
    city_id: int

    pickup_lat: float
    pickup_lng: float
    pickup_address: str

    drop_lat: float
    drop_lng: float
    drop_address: str

    vehicle_category: VehicleCategoryEnum
    fare_amount: float


class TripResponse(BaseModel):
    trip_id: int
    status: str
    fare_amount: float | None

    class Config:
        from_attributes = True

class TripFareEstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    vehicle_category: VehicleCategoryEnum


class TenantFareEstimate(BaseModel):
    tenant_id: int
    tenant_name: str
    fare: float
    breakup: dict


class TripFareEstimateResponse(BaseModel):
    city_id: int
    pickup_address: str | None
    drop_address: str | None
    distance_km: float
    vehicle_category: VehicleCategoryEnum
    estimates: List[TenantFareEstimate]