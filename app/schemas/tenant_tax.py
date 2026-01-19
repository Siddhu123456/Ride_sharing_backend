from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TenantTaxRuleCreateRequest(BaseModel):
    country_code: str                 # "IN", "US"
    tax_type: Optional[str] = None    # "GST", "VAT"
    rate: float                       # 5.00
    effective_from: datetime          # "2026-01-01T00:00:00Z"
    effective_to: Optional[datetime] = None


class TenantTaxRuleResponse(BaseModel):
    tax_id: int
    tenant_id: int
    country_code: str
    tax_type: Optional[str]
    rate: float
    effective_from: datetime
    effective_to: Optional[datetime]
    created_by: str
    created_on: datetime

    class Config:
        from_attributes = True
