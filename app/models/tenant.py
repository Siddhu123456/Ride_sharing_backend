from sqlalchemy import (
    Column, BigInteger, String, Boolean, Date, TIMESTAMP, ForeignKey,
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

    tenant_country_id = Column(BigInteger, primary_key=True, index=True)
    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)
    country_code = Column(String(2), ForeignKey("country.country_code"), nullable=False)

    is_active = Column(Boolean, default=True)
    launched_on = Column(Date, nullable=True)
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "country_code", name="uq_tenant_country"),
    )


class City(Base):
    __tablename__ = "city"

    city_id = Column(BigInteger, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_code"), nullable=False)

    name = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    currency = Column(String(3), nullable=False)

    __table_args__ = (
        UniqueConstraint("country_code", "name", name="uq_city_country_name"),
    )


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