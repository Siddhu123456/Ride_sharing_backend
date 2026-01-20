from sqlalchemy import (
    Column, BigInteger, ForeignKey,
    TIMESTAMP, Text, func
)
from app.models.base import Base

class DispatchAttempt(Base):
    __tablename__ = "dispatch_attempt"

    attempt_id = Column(BigInteger, primary_key=True, index=True)

    trip_id = Column(
        BigInteger,
        ForeignKey("trip.trip_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False, index=True)

    sent_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    responded_at = Column(TIMESTAMP(timezone=True), nullable=True)

    response = Column(Text, nullable=True)  # ACCEPTED / REJECTED / TIMEOUT

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    updated_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)
