from sqlalchemy import (
    CHAR, VARCHAR, Column, BigInteger, String, Boolean, Date, TIMESTAMP, ForeignKey,
    UniqueConstraint, func
)

from app.models.base import Base

class Tenant(Base):
    __tablename__ = "tenant"

    tenant_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    default_currency = Column(String(3), nullable=False)
    default_timezone = Column(String, nullable=False)

    status = Column(String, default="ACTIVE")
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now())


class TenantCountry(Base):
    __tablename__ = "tenant_country"

    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), primary_key=True)
    country_code = Column(CHAR(2), ForeignKey("country.country_code"), primary_key=True)
    launched_on = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(VARCHAR(20), nullable=False, server_default="admin")
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    updated_by = Column(BigInteger, ForeignKey("app_user.user_id"), nullable=True)
    updated_on = Column(TIMESTAMP(timezone=True), nullable=True)






class TenantCity(Base):
    __tablename__ = "tenant_city"

    tenant_city_id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)
    city_id = Column(BigInteger, ForeignKey("city.city_id"), nullable=False)

    is_active = Column(Boolean, default=True)
    launched_on = Column(Date, nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "city_id", name="uq_tenant_city"),
    )