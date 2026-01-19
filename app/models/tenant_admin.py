from sqlalchemy import Column, BigInteger, Boolean, TIMESTAMP, ForeignKey, func, UniqueConstraint
from app.models.base import Base


class TenantAdmin(Base):
    __tablename__ = "tenant_admin"

    tenant_admin_id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=False)

    is_primary = Column(Boolean, nullable=False, server_default="false")
    is_active = Column(Boolean, nullable=False, server_default="true")

    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_admin"),
    )
