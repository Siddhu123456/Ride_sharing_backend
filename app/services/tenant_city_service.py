from sqlalchemy import select

from app.models.tenant import TenantCity


def tenant_operates_in_city(db, tenant_id: int, city_id: int) -> bool:
    return db.execute(
        select(TenantCity).where(
            TenantCity.tenant_id == tenant_id,
            TenantCity.city_id == city_id,
            TenantCity.is_active == True
        )
    ).scalar_one_or_none() is not None
