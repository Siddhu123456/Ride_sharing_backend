from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum
from app.schemas.trip import TripFareEstimateRequest, TripFareEstimateResponse

from app.services.location_service import detect_city_by_location
from app.services.geo_coding_service import reverse_geocode
from app.services.distance_service import calculate_distance_km
from app.services.fare_service import calculate_fare
from app.services.tenant_city_service import get_tenants_operating_in_city

router = APIRouter(prefix="/trips", tags=["Trips - Fare Discovery"])


@router.post("/fare-estimate", response_model=TripFareEstimateResponse)
def get_fare_estimates(
    payload: TripFareEstimateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(TenantRoleEnum.RIDER))
):
    # 1️⃣ Detect city
    city_id = detect_city_by_location(
        db, payload.pickup_lat, payload.pickup_lng
    )
    if not city_id:
        raise HTTPException(400, "Pickup outside service area")

    # 2️⃣ Reverse geocode
    pickup_address = reverse_geocode(payload.pickup_lat, payload.pickup_lng)
    drop_address = reverse_geocode(payload.drop_lat, payload.drop_lng)

    # 3️⃣ Distance
    distance_km = calculate_distance_km(
        payload.pickup_lat,
        payload.pickup_lng,
        payload.drop_lat,
        payload.drop_lng
    )

    # 4️⃣ Tenants operating in city
    tenants = get_tenants_operating_in_city(db, city_id)

    estimates = []

    for tenant in tenants:
        try:
            fare = calculate_fare(
                db=db,
                tenant_id=tenant.tenant_id,
                city_id=city_id,
                vehicle_category=payload.vehicle_category,
                distance_km=distance_km
            )

            estimates.append({
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.name,
                "fare": fare["total_fare"],
                "breakup": fare
            })
        except Exception:
            # tenant doesn't support this vehicle type
            continue

    if not estimates:
        raise HTTPException(404, "No available rides")

    return {
        "city_id": city_id,
        "pickup_address": pickup_address,
        "drop_address": drop_address,
        "distance_km": distance_km,
        "vehicle_category": payload.vehicle_category,
        "estimates": estimates
    }
