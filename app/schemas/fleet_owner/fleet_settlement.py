from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from app.schemas.enums import SettlementStatusEnum


class FleetSettlementTripItem(BaseModel):
    trip_id: int
    commission_amount: Decimal


class FleetSettlementResponse(BaseModel):
    settlement_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime
    paid_on: datetime | None
    trips: List[FleetSettlementTripItem]


class FleetSettlementPayResponse(BaseModel):
    settlement_id: int
    status: SettlementStatusEnum
    paid_on: datetime


class SettlementTripItem(BaseModel):
    trip_id: int
    commission_amount: Decimal

    model_config = {
        "from_attributes": True
    }


class SettlementTransactionItem(BaseModel):
    transaction_id: int
    wallet_id: int
    amount: Decimal
    direction: str
    reason: str
    created_on: datetime

    model_config = {
        "from_attributes": True
    }


class FleetSettlementHistoryItem(BaseModel):
    settlement_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime
    paid_on: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
