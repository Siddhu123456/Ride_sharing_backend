from sqlalchemy import (
    Column, BigInteger, String, TIMESTAMP, ForeignKey,
    Enum, func
)
from app.models.base import Base
from app.schemas.enums import AccountStatusEnum, ApprovalStatusEnum  # match your enums


class Fleet(Base):
    __tablename__ = "fleet"

    fleet_id = Column(BigInteger, primary_key=True, index=True)

    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)
    owner_user_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)

    fleet_name = Column(String(150), nullable=False)

    status = Column(Enum(AccountStatusEnum, name="account_status_enum"), nullable=False, server_default="INACTIVE")
    approval_status = Column(Enum(ApprovalStatusEnum, name="approval_status_enum"), nullable=False, server_default="PENDING")

    verified_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    verified_on = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)
