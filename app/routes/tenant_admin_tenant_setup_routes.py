# app/routes/tenant_admin_tenant_setup_routes.py
# ---------------------------------------------------------
# Tenant Admin Tenant Setup (JWT + role TENANT_ADMIN)
# ---------------------------------------------------------

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.tenant_admin_guard import get_tenant_admin

from app.models.tenant import Tenant, TenantCity, TenantCountry
from app.models.core import City
from app.models.tenant_admin import TenantAdmin

from app.schemas.admin_tenant import (
    TenantCountryCreateRequest,
    TenantCountryResponse,
    BulkCitiesCreateRequest,
    BulkCitiesCreateResponse,
    CityResponse,
)

router = APIRouter(
    prefix="/tenant-admin",
    tags=["Tenant Admin - Tenant Setup"]
)

# =========================================================
# 3) BULK ADD CITIES UNDER TENANT + COUNTRY
# =========================================================
@router.post(
    "/tenants/{tenant_id}/countries/{country_code}/cities",
    response_model=BulkCitiesCreateResponse,
    status_code=status.HTTP_201_CREATED
)
def bulk_add_cities_for_tenant_country(
    tenant_id: int,
    country_code: str,
    payload: BulkCitiesCreateRequest,
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    # ✅ ensure tenant exists
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # ✅ ensure tenant has this country enabled and active
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

        # ✅ 1) Check if city exists in master city table
        city = db.execute(
            select(City).where(
                and_(
                    City.country_code == country_code,
                    City.name == city_name
                )
            )
        ).scalar_one_or_none()

        # ✅ 2) If not exists → create
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

        # ✅ 3) Map into tenant_city if not already mapped
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
# 4) LIST TENANT CITIES (optional filter by country_code)
# =========================================================
@router.get(
    "/tenants/{tenant_id}/cities",
    response_model=List[CityResponse]
)
def list_tenant_cities(
    tenant_id: int,
    country_code: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

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
