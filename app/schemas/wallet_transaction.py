from pydantic import BaseModel
from decimal import Decimal

class WalletTransactionResponse(BaseModel):
    transaction_id: int
    amount: Decimal
    transaction_type: str
