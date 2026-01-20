from sqlalchemy import Column, BigInteger, ForeignKey, Numeric
from app.models.base import Base


class TripFareBreakdown(Base):
    __tablename__ = "trip_fare_breakdown"

    id = Column(BigInteger, primary_key=True, index=True)

    trip_id = Column(BigInteger, ForeignKey("trip.trip_id"), nullable=False, index=True)

    base_fare = Column(Numeric(10, 2))
    distance_fare = Column(Numeric(10, 2))
    time_fare = Column(Numeric(10, 2))
    surge_amount = Column(Numeric(10, 2))
    tax_amount = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2))

    final_fare = Column(Numeric(10, 2), nullable=False)
