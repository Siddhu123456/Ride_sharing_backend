from sqlalchemy import Column, BigInteger, Numeric, Enum, TIMESTAMP, func
from app.models.base import Base
from app.schemas.enums import WalletOwnerEnum

class Wallet(Base):
    __tablename__ = "wallet"

    wallet_id = Column(BigInteger, primary_key=True)
    owner_type = Column(
    Enum(
        WalletOwnerEnum,
        name="wallet_owner_enum",
        create_type=False
    ),
    nullable=False
)

    owner_id = Column(BigInteger, nullable=False)
    balance = Column(Numeric(12,2), default=0)

    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now())
