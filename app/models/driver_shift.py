from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, Numeric, Text, func
from app.models.base import Base


class DriverShift(Base):
    __tablename__ = "driver_shift"

    shift_id = Column(BigInteger, primary_key=True, index=True)

    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)
    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)

    # ✅ store which vehicle this shift is using (from assignment)
    vehicle_id = Column(BigInteger, ForeignKey("vehicle.vehicle_id"), nullable=True)

    status = Column(Text, nullable=False)  # ONLINE / OFFLINE / ON_TRIP
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # ✅ when assignment ends, shift should end automatically
    expected_end_at = Column(TIMESTAMP(timezone=True), nullable=True)

    last_latitude = Column(Numeric(9, 6), nullable=True)
    last_longitude = Column(Numeric(9, 6), nullable=True)
