from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, UniqueConstraint, func, Time, Boolean, DateTime
from app.models.base import Base

class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignment"

    assignment_id = Column(BigInteger, primary_key=True)
    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"))
    vehicle_id = Column(BigInteger, ForeignKey("vehicle.vehicle_id"))

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    is_active = Column(Boolean, default=True)

    created_by = Column(BigInteger)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
