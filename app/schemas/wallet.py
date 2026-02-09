from pydantic import BaseModel
from decimal import Decimal

class WalletResponse(BaseModel):
    wallet_id: int
    balance: Decimal

    class Config:
        from_attributes = True
