from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.tenant import TenantCity, Tenant
from app.schemas.enums import AccountStatusEnum


def get_tenants_operating_in_city(
    db: Session,
    city_id: int
) -> list[Tenant]:
    """
    Returns all ACTIVE tenants operating in a given city
    """

    stmt = (
        select(Tenant)
        .join(
            TenantCity,
            Tenant.tenant_id == TenantCity.tenant_id
        )
        .where(
            and_(
                TenantCity.city_id == city_id,
                TenantCity.is_active == True,
                Tenant.status == AccountStatusEnum.ACTIVE
            )
        )
    )

    return db.execute(stmt).scalars().all()


def tenant_operates_in_city(db, tenant_id: int, city_id: int) -> bool:
    return db.execute(
        select(TenantCity).where(
            TenantCity.tenant_id == tenant_id,
            TenantCity.city_id == city_id,
            TenantCity.is_active == True
        )
    ).scalar_one_or_none() is not None
