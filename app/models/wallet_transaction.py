from sqlalchemy import Column, BigInteger, Numeric, Enum, TIMESTAMP, ForeignKey, func
from app.models.base import Base
from app.schemas.enums import WalletTxnTypeEnum

class WalletTransaction(Base):
    __tablename__ = "wallet_transaction"

    transaction_id = Column(BigInteger, primary_key=True)
    wallet_id = Column(BigInteger, ForeignKey("wallet.wallet_id"))
    trip_id = Column(BigInteger, ForeignKey("trip.trip_id"))

    amount = Column(Numeric(10, 2), nullable=False)

    transaction_type = Column(
        Enum(
            WalletTxnTypeEnum,
            name="wallet_txn_type_enum",
            create_type=False
        ),
        nullable=False
    )

    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now())
