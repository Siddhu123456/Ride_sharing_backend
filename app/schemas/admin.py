from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# Tenant (admin) models
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


# Tenant tax rules
class TenantTaxRuleCreateRequest(BaseModel):
    country_code: str                 # "IN", "US"
    tax_type: Optional[str] = None    # "GST", "VAT"
    rate: float                       # 5.00
    effective_from: datetime          # "2026-01-01T00:00:00Z"
    effective_to: Optional[datetime] = None


class TenantTaxRuleResponse(BaseModel):
    tax_id: int
    tenant_id: int
    country_code: str
    tax_type: Optional[str]
    rate: float
    effective_from: datetime
    effective_to: Optional[datetime]
    created_by: str
    created_on: datetime

    class Config:
        from_attributes = True
