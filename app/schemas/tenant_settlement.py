from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List
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
