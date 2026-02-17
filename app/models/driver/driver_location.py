from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, Numeric, func
from app.models.base import Base

class DriverLocation(Base):
    __tablename__ = "driver_location"

    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), primary_key=True)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    last_updated = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
