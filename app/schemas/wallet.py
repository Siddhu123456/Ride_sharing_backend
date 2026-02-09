from typing import Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from app.schemas.enums import WalletOwnerEnum, WalletTxnTypeEnum

class WalletResponse(BaseModel):
    wallet_id: int
    balance: Decimal

    class Config:
        from_attributes = True


class WalletTransactionItem(BaseModel):
    transaction_id: int
    trip_id: Optional[int]

    amount: Decimal
    transaction_type: WalletTxnTypeEnum

    created_on: datetime


class WalletTransactionListResponse(BaseModel):
    wallet_id: int
    owner_type: WalletOwnerEnum
    owner_id: int

    balance: Decimal

    transactions: list[WalletTransactionItem]

    page: int
    limit: int
    total: int