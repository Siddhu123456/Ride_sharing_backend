from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from app.schemas.enums import (
    WalletOwnerEnum,
    WalletTxnReasonEnum,
    WalletTxnDirectionEnum
)

# -------------------------------------------------
# Wallet
# -------------------------------------------------

class WalletResponse(BaseModel):
    wallet_id: int
    balance: Decimal

    class Config:
        from_attributes = True


# -------------------------------------------------
# Wallet Transaction Item
# -------------------------------------------------

class WalletTransactionItem(BaseModel):
    transaction_id: int
    trip_id: Optional[int]

    amount: Decimal
    direction: WalletTxnDirectionEnum
    reason: WalletTxnReasonEnum

    created_on: datetime

    model_config = {
        "from_attributes": True
    }


# -------------------------------------------------
# Paginated Response
# -------------------------------------------------

class WalletTransactionListResponse(BaseModel):
    wallet_id: int
    owner_type: WalletOwnerEnum
    owner_id: int

    balance: Decimal
    transactions: List[WalletTransactionItem]

    page: int
    limit: int
    total: int

    model_config = {
        "from_attributes": True
    }
