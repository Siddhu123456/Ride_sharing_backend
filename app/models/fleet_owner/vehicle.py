from sqlalchemy import Column, BigInteger, String, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum, VehicleCategoryEnum, VehicleStatusEnum

class Vehicle(Base):
    __tablename__ = "vehicle"

    vehicle_id = Column(BigInteger, primary_key=True, index=True)

    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False, index=True)
    fleet_id = Column(BigInteger, ForeignKey("fleet.fleet_id"), nullable=True, index=True)

    category = Column(ENUM(VehicleCategoryEnum, name="vehicle_category_enum"), nullable=False)

    status = Column(
        ENUM(VehicleStatusEnum, name="vehicle_status_enum"),
        nullable=False,
        server_default="INACTIVE"
    )

    approval_status = Column(
        ENUM(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    registration_no = Column(String(50), unique=True, nullable=False)
    make = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year_of_manufacture = Column(Integer, nullable=True)

    verified_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    verified_on = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)
