from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenant"

    tenant_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    support_email = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())