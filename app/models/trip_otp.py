from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, Boolean, String
from sqlalchemy.sql import func
from app.models.base import Base


class TripOtp(Base):
    __tablename__ = "trip_otp"

    otp_id = Column(BigInteger, primary_key=True, index=True)

    trip_id = Column(
        BigInteger,
        ForeignKey("trip.trip_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    otp_code = Column(String(10), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    verified = Column(Boolean, nullable=False, server_default="false")
