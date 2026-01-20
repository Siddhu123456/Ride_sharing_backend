from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, UniqueConstraint, func
from app.models.base import Base

class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignment"

    assignment_id = Column(BigInteger, primary_key=True, index=True)
    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)
    vehicle_id = Column(BigInteger, ForeignKey("vehicle.vehicle_id"), nullable=False)

    start_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"))

    __table_args__ = (
        UniqueConstraint("driver_id", "vehicle_id", "start_time", name="uq_driver_vehicle_start"),
    )
