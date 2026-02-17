from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, Numeric, func
from app.models.base import Base

class DriverLocationHistory(Base):
    __tablename__ = "driver_location_history"

    id = Column(BigInteger, primary_key=True, index=True)
    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)

    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)

    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
