from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any
from pydantic import BaseModel
from app.schemas.enums import VehicleCategoryEnum


class CityResponse(BaseModel):
    city_id: int
    country_code: str
    name: str
    timezone: str
    currency: str
    boundary: Optional[Any] = None  # GeoJSON or None
    created_on: datetime

    class Config:
        from_attributes = True


class CityBoundaryUpdateRequest(BaseModel):
    boundary_geojson: dict


class FareConfigCreateInput(BaseModel):
    vehicle_category: VehicleCategoryEnum

    base_fare: Decimal
    per_km_rate: Decimal
    per_min_rate: Decimal

    minimum_fare: Optional[Decimal] = None
    platform_commission_percent: Decimal  


class CityCreateWithFareRequest(BaseModel):
    name: str
    timezone: str
    currency: str

    fare_configs: List[FareConfigCreateInput] 


class FareConfigResponse(BaseModel):
    fare_config_id: int
    vehicle_category: VehicleCategoryEnum
    base_fare: float
    per_km_rate: float
    per_min_rate: float
    minimum_fare: float | None
    platform_commission_percent: float

    class Config:
        from_attributes = True


class CityWithFareResponse(BaseModel):
    city_id: int
    name: str
    country_code: str

    fare_configs: List[FareConfigResponse]
    created_on: datetime

    class Config:
        from_attributes = True


class FareConfigUpdateRequest(BaseModel):
    base_fare: Optional[Decimal] = None
    per_km_rate: Optional[Decimal] = None
    per_min_rate: Optional[Decimal] = None
    minimum_fare: Optional[Decimal] = None
    platform_commission_percent: Optional[Decimal] = None
    is_active: Optional[bool] = None
