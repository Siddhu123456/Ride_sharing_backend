from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from app.schemas.enums import ApprovalStatusEnum, DriverTypeEnum, SettlementStatusEnum


# --- Tenant admin assignments ---
class AssignTenantAdminRequest(BaseModel):
    user_id: int
    is_primary: bool = False


class TenantAdminResponse(BaseModel):
    tenant_admin_id: int
    tenant_id: int
    user_id: int
    is_primary: bool
    is_active: bool
    created_on: datetime

    class Config:
        from_attributes = True


class TenantAdminListResponse(BaseModel):
    tenant_id: int
    admins: List[TenantAdminResponse]


class RemoveTenantAdminResponse(BaseModel):
    message: str
    

# --- Tenant admin profile ---
class TenantAdminProfileResponse(BaseModel):
    user_id: int
    full_name: str
    phone: str
    email: str | None
    gender: str | None

    tenant_id: int
    tenant_name: str

    countries: List[str]

    created_on: datetime

    model_config = {
        "from_attributes": True
    }


# --- Tenant settlements ---
class TenantSettlementTripItem(BaseModel):
    trip_id: int
    commission_amount: Decimal


class TenantSettlementCreateResponse(BaseModel):
    settlement_id: int
    fleet_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime


class TenantSettlementDetailResponse(BaseModel):
    settlement_id: int
    fleet_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime
    paid_on: datetime | None
    trips: List[TenantSettlementTripItem]


class TenantUnsettledTripItem(BaseModel):
    trip_id: int
    platform_fee: Decimal
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TenantFleetPendingCommission(BaseModel):
    fleet_id: int
    total_unsettled_trips: int
    total_commission: Decimal


class TenantSettlementHistoryItem(BaseModel):
    settlement_id: int
    fleet_id: int
    total_commission: Decimal
    status: str
    created_on: datetime
    paid_on: Optional[datetime]

    model_config = {"from_attributes": True}
    

class FleetResponse(BaseModel):
    fleet_id: int
    fleet_name: str

    model_config = {
        "from_attributes": True  
    }




