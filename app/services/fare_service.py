from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.fare_config import FareConfig
from app.services.tax_service import get_tax_amount


def calculate_fare(
    db: Session,
    tenant_id: int,
    city_id: int,
    vehicle_category,
    distance_km: float,
    duration_minutes: float = 0
):
    """
    Uses ACTIVE + LATEST fare_config
    """

    config = db.execute(
        select(FareConfig)
        .where(
            and_(
                FareConfig.tenant_id == tenant_id,
                FareConfig.city_id == city_id,
                FareConfig.vehicle_category == vehicle_category,
                FareConfig.is_active == True,
                FareConfig.effective_to.is_(None)
            )
        )
        .order_by(FareConfig.effective_from.desc())
    ).scalar_one_or_none()

    if not config:
        raise ValueError("Fare configuration not found")

    base = float(config.base_fare)
    distance_fare = distance_km * float(config.per_km_rate)
    time_fare = duration_minutes * float(config.per_min_rate)

    subtotal = base + distance_fare + time_fare

    if config.minimum_fare:
        subtotal = max(subtotal, float(config.minimum_fare))

    tax = get_tax_amount(db, tenant_id, subtotal)

    return {
        "base_fare": base,
        "distance_fare": distance_fare,
        "time_fare": time_fare,
        "tax": tax,
        "total_fare": subtotal + tax
    }
