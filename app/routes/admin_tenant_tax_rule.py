from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from starlette import status

from app.core.database import get_db
from app.core.admin_auth import verify_admin
from app.models.tenant import Tenant
from app.models.country import Country
from app.models.tenant_tax_rule import TenantTaxRule
from app.schemas.tenant_tax import TenantTaxRuleCreateRequest, TenantTaxRuleResponse

router = APIRouter(prefix="/admin/tenants", tags=["Admin Tenant Tax Rules"])


@router.post(
    "/{tenant_id}/tax-rules",   # ✅ FIXED PATH
    response_model=TenantTaxRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin)]
)
def add_tenant_tax_rule(
    tenant_id: int,
    payload: TenantTaxRuleCreateRequest,
    db: Session = Depends(get_db),
):
    # ✅ 1) Validate Tenant
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # ✅ 2) Validate Country
    country = db.execute(
        select(Country).where(Country.country_code == payload.country_code)
    ).scalar_one_or_none()

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # ✅ 3) Validate date logic
    if payload.effective_to is not None and payload.effective_to <= payload.effective_from:
        raise HTTPException(
            status_code=400,
            detail="effective_to must be greater than effective_from"
        )

    # ✅ 4) Overlap Check
    query = select(TenantTaxRule).where(
        TenantTaxRule.tenant_id == tenant_id,
        TenantTaxRule.country_code == payload.country_code
    )

    if payload.effective_to is not None:
        # new_start < existing_end AND existing_start < new_end
        query = query.where(
            TenantTaxRule.effective_from < payload.effective_to,
            or_(
                TenantTaxRule.effective_to.is_(None),
                TenantTaxRule.effective_to > payload.effective_from
            )
        )
    else:
        # Open ended rule
        query = query.where(
            or_(
                TenantTaxRule.effective_to.is_(None),
                TenantTaxRule.effective_to > payload.effective_from
            )
        )

    existing = db.execute(query).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A conflicting tax rule already exists for this date range"
        )

    # ✅ 5) Insert New Tax Rule (use correct column names)
    new_rule = TenantTaxRule(
        tenant_id=tenant_id,
        country_code=payload.country_code,
        tax_type=payload.tax_type,
        rate=payload.rate,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        created_by=None  # platform admin
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule
