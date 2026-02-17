from sqlalchemy import Column, BigInteger, Numeric, ForeignKey
from app.models.base import Base


class CommissionSettlementTrip(Base):
    __tablename__ = "commission_settlement_trip"

    id = Column(BigInteger, primary_key=True)

    settlement_id = Column(
        BigInteger,
        ForeignKey("commission_settlement.settlement_id", ondelete="CASCADE"),
        nullable=False
    )

    trip_id = Column(
        BigInteger,
        ForeignKey("trip.trip_id"),
        nullable=False,
        unique=True
    )

    commission_amount = Column(Numeric(10, 2), nullable=False)
