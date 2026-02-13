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
from app.services.driver_availability_service import (
    count_available_drivers_by_vehicle
)


router = APIRouter(prefix="/trips", tags=["Trips - Fare Discovery"])


@router.post("/fare-estimate", response_model=TripFareEstimateResponse)
def get_fare_estimates(
    payload: TripFareEstimateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(TenantRoleEnum.RIDER))
):
    # 1) Detect city by pickup location
    city_id = detect_city_by_location(
        db, payload.pickup_lat, payload.pickup_lng
    )
    if not city_id:
        raise HTTPException(400, "Pickup outside service area")

    # 2) Compute distance in kilometers
    distance_km = calculate_distance_km(
        payload.pickup_lat,
        payload.pickup_lng,
        payload.drop_lat,
        payload.drop_lng
    )

    # 3) Find tenants operating in the city
    tenants = get_tenants_operating_in_city(db, city_id)

    estimates = []

    for tenant in tenants:

    # Get availability for all vehicle categories
        availability_map = count_available_drivers_by_vehicle(
            db=db,
            city_id=city_id,
            tenant_id=tenant.tenant_id,
            pickup_lat=payload.pickup_lat,
            pickup_lng=payload.pickup_lng
        )

        for vehicle_category, driver_count in availability_map.items():
            try:
                fare = calculate_fare(
                    db=db,
                    tenant_id=tenant.tenant_id,
                    city_id=city_id,
                    vehicle_category=vehicle_category,
                    distance_km=distance_km
                )

                estimates.append({
                    "tenant_id": tenant.tenant_id,
                    "tenant_name": tenant.name,

                    "vehicle_category": vehicle_category,
                    "fare": fare["total_fare"],

                    "available_drivers": driver_count,
                    "breakup": fare
                })

            except Exception:
                # fare config not available for this vehicle
                continue

    if not estimates:
        raise HTTPException(404, "No available rides")

    return {
        "city_id": city_id,
        "pickup_address": payload.pickup_address,
        "drop_address": payload.drop_address,
        "distance_km": distance_km,
        "estimates": estimates
    }

