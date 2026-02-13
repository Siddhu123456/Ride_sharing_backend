from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from app.schemas.enums import SettlementStatusEnum


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