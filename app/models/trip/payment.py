from sqlalchemy import Column, BigInteger, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import Base
from app.schemas.enums import PaymentStatusEnum


class Payment(Base):
    __tablename__ = "payment"

    payment_id = Column(BigInteger, primary_key=True, index=True)

    trip_id = Column(BigInteger, ForeignKey("trip.trip_id"), nullable=False, index=True)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)

    payment_mode = Column(String, nullable=True)  # ONLINE / OFFLINE (you can enum later)

    status = Column(
        ENUM(PaymentStatusEnum, name="payment_status_enum"),
        nullable=False
    )
