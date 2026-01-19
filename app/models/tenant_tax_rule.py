from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, Numeric, func
from app.models.base import Base

class TenantTaxRule(Base):
    __tablename__ = "tenant_tax_rule"

    tax_id = Column(BigInteger, primary_key=True, index=True)

    tenant_id = Column(BigInteger, ForeignKey("tenant.tenant_id"), nullable=False)
    country_code = Column(String(2), ForeignKey("country.country_code"), nullable=False)

    tax_type = Column(String(50), nullable=True)
    rate = Column(Numeric(5, 2), nullable=False)

    effective_from = Column(TIMESTAMP(timezone=True), nullable=False)
    effective_to = Column(TIMESTAMP(timezone=True), nullable=True)

    created_by = Column(String(20), nullable=False, default="admin")
    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
