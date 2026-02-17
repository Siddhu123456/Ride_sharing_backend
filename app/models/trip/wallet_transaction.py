from sqlalchemy import (
    Column, BigInteger, Numeric, TIMESTAMP, ForeignKey, Enum, func
)
from app.models.base import Base
from app.schemas.enums import (
    WalletTxnReasonEnum,
    WalletTxnDirectionEnum
)

class WalletTransaction(Base):
    __tablename__ = "wallet_transaction"

    transaction_id = Column(BigInteger, primary_key=True, index=True)

    wallet_id = Column(
        BigInteger,
        ForeignKey("wallet.wallet_id"),
        nullable=False
    )

    trip_id = Column(
        BigInteger,
        ForeignKey("trip.trip_id"),
        nullable=True
    )

    amount = Column(Numeric(12, 2), nullable=False)

    direction = Column(
        Enum(
            WalletTxnDirectionEnum,
            name="wallet_txn_direction_enum",
            create_type=False
        ),
        nullable=False
    )

    reason = Column(
        Enum(
            WalletTxnReasonEnum,
            name="wallet_txn_reason_enum",
            create_type=False
        ),
        nullable=False
    )

    created_on = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
