# ---------------------------------------------------------
# Router
# ---------------------------------------------------------
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.admin_auth import verify_admin
from app.core.database import get_db
from app.models.tenant import  Tenant,  TenantCountry
from app.schemas.admin_tenant import  TenantCountryCreateRequest, TenantCountryResponse, TenantCreateRequest, TenantResponse



router = APIRouter(prefix="/admin", tags=["Admin Tenant Setup"])


# =========================================================
# 1) CREATE TENANT
# =========================================================
@router.post(
    "/tenants",
    response_model=TenantResponse,
    dependencies=[Depends(verify_admin)]
)
def create_tenant(payload: TenantCreateRequest, db: Session = Depends(get_db)):

    # check duplicate tenant name
    existing = db.execute(
        select(Tenant).where(Tenant.name == payload.name)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Tenant with this name already exists")

    tenant = Tenant(
        name=payload.name,
        default_currency=payload.default_currency,
        default_timezone=payload.default_timezone
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# =========================================================
# 2) LIST TENANTS
# =========================================================
@router.get(
    "/tenants",
    response_model=List[TenantResponse],
    dependencies=[Depends(verify_admin)]
)
def list_tenants(db: Session = Depends(get_db)):
    tenants = db.execute(select(Tenant)).scalars().all()
    return tenants


# =========================================================
# 3) ADD COUNTRY TO TENANT
# =========================================================
@router.post(
    "/tenants/{tenant_id}/countries",
    response_model=TenantCountryResponse,
    dependencies=[Depends(verify_admin)]
)
def add_country_to_tenant(
    tenant_id: int,
    payload: TenantCountryCreateRequest,
    db: Session = Depends(get_db)
):
    # ensure tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # check if already added
    existing = db.execute(
        select(TenantCountry).where(
            and_(
                TenantCountry.tenant_id == tenant_id,
                TenantCountry.country_code == payload.country_code
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Country already added for this tenant")

    tenant_country = TenantCountry(
        tenant_id=tenant_id,
        country_code=payload.country_code,
        launched_on=payload.launched_on
    )

    db.add(tenant_country)
    db.commit()
    db.refresh(tenant_country)
    return tenant_country


# =========================================================
# 4) LIST TENANT COUNTRIES
# =========================================================
@router.get(
    "/tenants/{tenant_id}/countries",
    response_model=List[TenantCountryResponse],
    dependencies=[Depends(verify_admin)]
)
def list_tenant_countries(tenant_id: int, db: Session = Depends(get_db)):

    # ensure tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    countries = db.execute(
        select(TenantCountry).where(TenantCountry.tenant_id == tenant_id)
    ).scalars().all()

    return countries
