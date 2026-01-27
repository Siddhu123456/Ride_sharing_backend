from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum
from app.models.trip import Trip
from app.models.user_session import UserSession

from app.schemas.trip import TripRequestCreate, TripResponse
from app.services.distance_service import calculate_distance_km
from app.services.fare_service import calculate_fare
from app.services.location_service import detect_city_by_location
from app.services.geo_coding_service import reverse_geocode
from app.services.tenant_city_service import tenant_operates_in_city

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("/request", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def request_trip(
    payload: TripRequestCreate,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    # 1️⃣ Detect city (PostGIS)
    city_id = detect_city_by_location(db, payload.pickup_lat, payload.pickup_lng)
    if not city_id:
        raise HTTPException(400, "Pickup outside service area")

    # 2️⃣ Tenant operates in city?
    if not tenant_operates_in_city(db, payload.tenant_id, city_id):
        raise HTTPException(403, "Tenant not operating here")

    # 3️⃣ Distance
    distance_km = calculate_distance_km(
        payload.pickup_lat,
        payload.pickup_lng,
        payload.drop_lat,
        payload.drop_lng
    )

    # 4️⃣ Fare (YOUR existing function)
    fare = calculate_fare(
        db=db,
        tenant_id=payload.tenant_id,
        city_id=city_id,
        vehicle_category=payload.vehicle_category,
        distance_km=distance_km
    )

    # 5️⃣ Reverse geocode (optional override)
    pickup_address = payload.pickup_address or reverse_geocode(
        payload.pickup_lat, payload.pickup_lng
    )
    drop_address = payload.drop_address or reverse_geocode(
        payload.drop_lat, payload.drop_lng
    )

    # 6️⃣ Create trip
    trip = Trip(
        tenant_id=payload.tenant_id,
        rider_id=session.user_id,
        city_id=city_id,

        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        pickup_address=pickup_address,

        drop_lat=payload.drop_lat,
        drop_lng=payload.drop_lng,
        drop_address=drop_address,

        vehicle_category=payload.vehicle_category,
        fare_amount=fare["total_fare"],
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip
