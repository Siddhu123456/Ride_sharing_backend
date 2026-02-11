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

from app.models.fare_config import FareConfig
from app.models.tenant import Tenant, TenantCity, TenantCountry
from app.models.core import City
from app.models.tenant_admin import TenantAdmin

from app.models.user import AppUser
from app.schemas.admin_tenant import (
    CityResponse,
)
from app.schemas.city import CityCreateWithFareRequest, CityWithFareResponse, FareConfigResponse, FareConfigUpdateRequest
from app.schemas.tenant_admin_profile import TenantAdminProfileResponse

router = APIRouter(
    prefix="/tenant-admin",
    tags=["Tenant Admin - Tenant Setup"]
)

@router.get(
    "/me/profile",
    response_model=TenantAdminProfileResponse
)
def get_tenant_admin_profile(
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    # Get user details
    user = db.execute(
        select(AppUser).where(
            AppUser.user_id == tenant_admin.user_id
        )
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    # Get tenant details
    tenant = db.execute(
        select(Tenant).where(
            Tenant.tenant_id == tenant_admin.tenant_id
        )
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Get enabled countries for tenant
    countries = db.execute(
        select(TenantCountry.country_code).where(
            TenantCountry.tenant_id == tenant_admin.tenant_id
        )
    ).scalars().all()

    return TenantAdminProfileResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        gender=user.gender,

        tenant_id=tenant.tenant_id,
        tenant_name=tenant.name,

        countries=countries,
        created_on=user.created_on
    )


@router.post(
    "/{tenant_id}/countries/{country_code}/city",
    response_model=CityWithFareResponse,
    status_code=status.HTTP_201_CREATED
)
def add_city_with_fare_config(
    tenant_id: int,
    country_code: str,
    payload: CityCreateWithFareRequest,
    db: Session = Depends(get_db),
    tenant_admin=Depends(get_tenant_admin),
):
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(403, "Not allowed")

    if not payload.fare_configs:
        raise HTTPException(400, "At least one fare config is required")

    # Validate tenant
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Validate tenant-country
    tenant_country = db.execute(
        select(TenantCountry).where(
            TenantCountry.tenant_id == tenant_id,
            TenantCountry.country_code == country_code
        )
    ).scalar_one_or_none()

    if not tenant_country:
        raise HTTPException(400, "Tenant not enabled for this country")

    city_name = payload.name.strip()

    # City master
    city = db.execute(
        select(City).where(
            City.country_code == country_code,
            City.name == city_name
        )
    ).scalar_one_or_none()

    if not city:
        city = City(
            country_code=country_code,
            name=city_name,
            timezone=payload.timezone,
            currency=payload.currency
        )
        db.add(city)
        db.flush()

    # Tenant-city mapping
    existing_map = db.execute(
        select(TenantCity).where(
            TenantCity.tenant_id == tenant_id,
            TenantCity.city_id == city.city_id
        )
    ).scalar_one_or_none()

    if existing_map:
        raise HTTPException(400, "City already mapped to tenant")

    db.add(
        TenantCity(
            tenant_id=tenant_id,
            city_id=city.city_id,
            is_active=True
        )
    )

    # Fare configs (mandatory)
    fare_rows = []

    for fc in payload.fare_configs:
        existing_fc = db.execute(
            select(FareConfig).where(
                FareConfig.city_id == city.city_id,
                FareConfig.vehicle_category == fc.vehicle_category
            )
        ).scalar_one_or_none()

        if existing_fc:
            raise HTTPException(
                400,
                f"Fare config already exists for {fc.vehicle_category}"
            )

        fare = FareConfig(
            tenant_id=tenant_id,
            city_id=city.city_id,
            vehicle_category=fc.vehicle_category,
            base_fare=fc.base_fare,
            per_km_rate=fc.per_km_rate,
            per_min_rate=fc.per_min_rate,
            minimum_fare=fc.minimum_fare,
            platform_commission_percent=fc.platform_commission_percent
        )

        db.add(fare)
        fare_rows.append(fare)

    db.commit()

    return CityWithFareResponse(
        city_id=city.city_id,
        name=city.name,
        country_code=city.country_code,
        fare_configs=fare_rows,
        created_on=city.created_on
    )


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


@router.get(
    "/{tenant_id}/cities/{city_id}/fare-configs",
    response_model=List[FareConfigResponse],
)
def get_city_fare_configs(
    tenant_id: int,
    city_id: int,
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(403, "Not allowed")

    # Validate city belongs to tenant
    mapping = db.execute(
        select(TenantCity).where(
            TenantCity.tenant_id == tenant_id,
            TenantCity.city_id == city_id,
            TenantCity.is_active == True
        )
    ).scalar_one_or_none()

    if not mapping:
        raise HTTPException(404, "City not mapped to this tenant")

    # Fetch fare configs
    fare_configs = db.execute(
        select(FareConfig).where(
            FareConfig.tenant_id == tenant_id,
            FareConfig.city_id == city_id,
            FareConfig.is_active == True
        )
    ).scalars().all()

    return fare_configs


@router.put(
    "/{tenant_id}/fare-config/{fare_config_id}",
    response_model=CityWithFareResponse
)
def update_fare_config(
    tenant_id: int,
    fare_config_id: int,
    payload: FareConfigUpdateRequest,
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(403, "Not allowed")

    fare = db.execute(
        select(FareConfig).where(
            FareConfig.fare_config_id == fare_config_id,
            FareConfig.tenant_id == tenant_id
        )
    ).scalar_one_or_none()

    if not fare:
        raise HTTPException(404, "Fare config not found")

    # Update only provided fields
    if payload.base_fare is not None:
        fare.base_fare = payload.base_fare

    if payload.per_km_rate is not None:
        fare.per_km_rate = payload.per_km_rate

    if payload.per_min_rate is not None:
        fare.per_min_rate = payload.per_min_rate

    if payload.minimum_fare is not None:
        fare.minimum_fare = payload.minimum_fare

    if payload.platform_commission_percent is not None:
        if payload.platform_commission_percent < 0 or payload.platform_commission_percent > 100:
            raise HTTPException(400, "Invalid commission percentage")
        fare.platform_commission_percent = payload.platform_commission_percent

    if payload.is_active is not None:
        fare.is_active = payload.is_active

    db.commit()
    db.refresh(fare)

    return fare


@router.get(
    "/{tenant_id}/countries/{country_code}/available-cities",
    response_model=List[CityResponse]
)
def get_available_cities_for_country(
    tenant_id: int,
    country_code: str,
    db: Session = Depends(get_db),
    tenant_admin: TenantAdmin = Depends(get_tenant_admin),
):
    # Tenant scope validation
    if tenant_admin.tenant_id != tenant_id:
        raise HTTPException(403, "Not allowed")

    # Validate tenant-country relationship
    tenant_country = db.execute(
        select(TenantCountry).where(
            TenantCountry.tenant_id == tenant_id,
            TenantCountry.country_code == country_code
        )
    ).scalar_one_or_none()

    if not tenant_country:
        raise HTTPException(
            400,
            "Tenant not enabled for this country"
        )

    # Subquery: cities already mapped to tenant
    mapped_cities_subquery = (
        select(TenantCity.city_id)
        .where(TenantCity.tenant_id == tenant_id)
    )

    # Fetch cities from master table excluding mapped ones
    available_cities = db.execute(
        select(City)
        .where(
            City.country_code == country_code,
            City.city_id.not_in(mapped_cities_subquery)
        )
        .order_by(City.name)
    ).scalars().all()

    return available_cities
