# ---------------------------------------------------------
# Router
# ---------------------------------------------------------
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.admin_auth import verify_admin
from app.core.database import get_db
from app.models.tenant import  Tenant, TenantCity, TenantCountry
from app.models.core import City
from app.schemas.admin_tenant import BulkCitiesCreateRequest, BulkCitiesCreateResponse, CityResponse, TenantCountryCreateRequest, TenantCountryResponse, TenantCreateRequest, TenantResponse



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


# =========================================================
# 5) BULK ADD CITIES UNDER TENANT + COUNTRY
# - Ensures tenant_country is enabled and active
# - Creates city master entries if missing
# - Maps cities into tenant_city
# =========================================================
@router.post(
    "/tenants/{tenant_id}/countries/{country_code}/cities",
    response_model=BulkCitiesCreateResponse,
    dependencies=[Depends(verify_admin)]
)
def bulk_add_cities_for_tenant_country(
    tenant_id: int,
    country_code: str,
    payload: BulkCitiesCreateRequest,
    db: Session = Depends(get_db)
):
    # ensure tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # ensure tenant has this country enabled and active
    tenant_country = db.execute(
        select(TenantCountry).where(
            and_(
                TenantCountry.tenant_id == tenant_id,
                TenantCountry.country_code == country_code,
            )
        )
    ).scalar_one_or_none()

    if not tenant_country:
        raise HTTPException(
            status_code=400,
            detail="Tenant does not have this country enabled or it is inactive"
        )

    created_cities: List[City] = []
    mapped_city_ids: List[int] = []
    skipped_city_names: List[str] = []

    for c in payload.cities:
        city_name = c.name.strip()

        # 1) Check if city exists in master city table
        city = db.execute(
            select(City).where(
                and_(
                    City.country_code == country_code,
                    City.name == city_name
                )
            )
        ).scalar_one_or_none()

        # 2) If not exists => create
        if not city:
            city = City(
                country_code=country_code,
                name=city_name,
                timezone=c.timezone,
                currency=c.currency
            )
            db.add(city)
            db.flush()  # get city_id
            created_cities.append(city)

        # 3) Map into tenant_city if not already mapped
        existing_map = db.execute(
            select(TenantCity).where(
                and_(
                    TenantCity.tenant_id == tenant_id,
                    TenantCity.city_id == city.city_id
                )
            )
        ).scalar_one_or_none()

        if existing_map:
            skipped_city_names.append(city.name)
            continue

        mapping = TenantCity(
            tenant_id=tenant_id,
            city_id=city.city_id,
            is_active=True
        )
        db.add(mapping)
        db.flush()
        mapped_city_ids.append(city.city_id)

    db.commit()

    return BulkCitiesCreateResponse(
        tenant_id=tenant_id,
        country_code=country_code,
        created_cities=created_cities,
        mapped_city_ids=mapped_city_ids,
        skipped_city_names=skipped_city_names
    )


# =========================================================
# 6) LIST TENANT CITIES (optionally filter by country_code)
# =========================================================
@router.get(
    "/tenants/{tenant_id}/cities",
    response_model=List[CityResponse],
    dependencies=[Depends(verify_admin)]
)
def list_tenant_cities(
    tenant_id: int,
    country_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # ensure tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    stmt = (
        select(City)
        .join(TenantCity, TenantCity.city_id == City.city_id)
        .where(TenantCity.tenant_id == tenant_id)
        .where(TenantCity.is_active == True)
    )

    if country_code:
        stmt = stmt.where(City.country_code == country_code)

    cities = db.execute(stmt).scalars().all()
    return cities