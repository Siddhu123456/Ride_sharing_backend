from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum
from app.models.trip.trip import Trip
from app.models.common.user_session import UserSession

from app.schemas.trip import CityCheckRequest, TripRequestCreate, TripResponse
from app.services.trip.location_service import detect_city_by_location
from app.services.trip.tenant_city_service import tenant_operates_in_city
from app.services.trip.dispatch_service import dispatch_trip


router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("/request", response_model=TripResponse, status_code=201)
def request_trip(
    payload: TripRequestCreate,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):

    if not tenant_operates_in_city(db, payload.tenant_id, payload.city_id):
        raise HTTPException(403, "Tenant not operating in this city")

    trip = Trip(
        tenant_id=payload.tenant_id,
        rider_id=session.user_id,
        city_id=payload.city_id,

        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        pickup_address=payload.pickup_address,

        drop_lat=payload.drop_lat,
        drop_lng=payload.drop_lng,
        drop_address=payload.drop_address,

        vehicle_category=payload.vehicle_category,
        fare_amount=payload.fare_amount,

        created_by=session.user_id
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # START DISPATCH
    dispatch_trip(db, trip, session.user_id)

    return trip


@router.post("/same-city", response_model=bool)
def check_same_city(
    payload: CityCheckRequest,
    db: Session = Depends(get_db)
):
    pickup_city = detect_city_by_location(
        db,
        payload.pickup_lat,
        payload.pickup_lng
    )

    drop_city = detect_city_by_location(
        db,
        payload.drop_lat,
        payload.drop_lng
    )

    # If either location not inside any city → treat as False
    if pickup_city is None or drop_city is None:
        return False

    return pickup_city == drop_city