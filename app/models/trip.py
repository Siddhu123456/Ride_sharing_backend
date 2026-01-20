from sqlalchemy import (
    Column, BigInteger, ForeignKey,
    TIMESTAMP, Numeric, func
)
from sqlalchemy.dialects.postgresql import ENUM

from app.models.base import Base
from app.schemas.enums import (
    TripStatusEnum,
    PaymentStatusEnum,
    VehicleCategoryEnum
)

class Trip(Base):
    __tablename__ = "trip"

    trip_id = Column(BigInteger, primary_key=True, index=True)

    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False, index=True)
    rider_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False, index=True)
    driver_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True, index=True)
    vehicle_id = Column(BigInteger, ForeignKey("vehicle.vehicle_id"), nullable=True, index=True)

    city_id = Column(BigInteger, ForeignKey("city.city_id"), nullable=False, index=True)
    zone_id = Column(BigInteger, ForeignKey("zone.zone_id"), nullable=True, index=True)

    pickup_lat = Column(Numeric(9, 6), nullable=False)
    pickup_lng = Column(Numeric(9, 6), nullable=False)
    drop_lat = Column(Numeric(9, 6), nullable=True)
    drop_lng = Column(Numeric(9, 6), nullable=True)

    vehicle_category = Column(
        ENUM(VehicleCategoryEnum, name="vehicle_category_enum"),
        nullable=False,
        server_default="BIKE"
    )

    status = Column(
        ENUM(TripStatusEnum, name="trip_status_enum"),
        nullable=False,
        server_default="REQUESTED"
    )

    requested_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    picked_up_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    cancelled_at = Column(TIMESTAMP(timezone=True), nullable=True)

    fare_amount = Column(Numeric(10, 2), nullable=True)
    driver_earning = Column(Numeric(10, 2), nullable=True)
    platform_fee = Column(Numeric(10, 2), nullable=True)

    payment_status = Column(
        ENUM(PaymentStatusEnum, name="payment_status_enum"),
        nullable=True,
        server_default="PENDING"
    )

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    updated_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)
