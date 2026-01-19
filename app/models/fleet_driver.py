from sqlalchemy import Column, BigInteger, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.schema import UniqueConstraint
from app.models.base import Base
from app.schemas.enums import ApprovalStatusEnum


class FleetDriver(Base):
    __tablename__ = "fleet_driver"

    id = Column(BigInteger, primary_key=True, index=True)

    fleet_id = Column(BigInteger, ForeignKey("fleet.fleet_id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(BigInteger, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=False, index=True)

    approval_status = Column(
        ENUM(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        server_default="PENDING"
    )

    start_date = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("fleet_id", "driver_id", "start_date", name="uq_fleet_driver_start"),
    )
