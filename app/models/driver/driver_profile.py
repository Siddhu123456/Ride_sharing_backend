from sqlalchemy import Column, BigInteger, ForeignKey, TIMESTAMP, Numeric, func
from sqlalchemy.dialects.postgresql import ENUM
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum, DriverTypeEnum


class DriverProfile(Base):
    __tablename__ = "driver_profile"

    driver_id = Column(
        BigInteger,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )

    tenant_id = Column(
        BigInteger,
        ForeignKey("tenant.tenant_id"),
        nullable=False,
        index=True
    )

    driver_type = Column(ENUM(DriverTypeEnum, name="driver_type_enum"), nullable=False)

    approval_status = Column(
        ENUM(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    rating = Column(Numeric(3, 2), server_default="5.00")

    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_on = Column(TIMESTAMP(timezone=True))
