from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TenantCreateRequest(BaseModel):
    name: str
    default_currency: str
    default_timezone: str


class TenantResponse(BaseModel):
    tenant_id: int
    name: str
    default_currency: str
    default_timezone: str
    status: str

    class Config:
        from_attributes = True


class TenantCountryCreateRequest(BaseModel):
    country_code: str
    launched_on: Optional[date] = None


class TenantCountryResponse(BaseModel):
    tenant_id: int
    country_code: str

    launched_on: Optional[datetime] = None

    created_by: str = Field(default="admin")
    created_on: datetime

    updated_by: Optional[int] = None
    updated_on: Optional[datetime] = None

    class Config:
        from_attributes = True  



class CityCreateRequest(BaseModel):
    name: str
    timezone: str
    currency: str


class BulkCitiesCreateRequest(BaseModel):
    cities: List[CityCreateRequest]


class CityResponse(BaseModel):
    city_id: int
    country_code: str
    name: str
    timezone: str
    currency: str

    class Config:
        from_attributes = True


class TenantCityResponse(BaseModel):
    tenant_city_id: int
    tenant_id: int
    city_id: int
    is_active: bool
    launched_on: Optional[date] = None

    class Config:
        from_attributes = True


class BulkCitiesCreateResponse(BaseModel):
    tenant_id: int
    country_code: str
    created_cities: List[CityResponse]
    mapped_city_ids: List[int]
    skipped_city_names: List[str]

