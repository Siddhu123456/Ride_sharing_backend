from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.trip.trip import Trip
from app.models.common.user_session import UserSession
from app.schemas.trip import NearbyDriverResponse, NearbyDriversListResponse, NearbyDriversRequest
from app.services.trip.driver_availability_service import get_online_drivers_within_10km

router = APIRouter(prefix="/rider/trips", tags=["Rider - Trips"])


@router.get("/active")
def get_active_trip_for_rider(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    active_statuses = [
        TripStatusEnum.REQUESTED,
        TripStatusEnum.ASSIGNED,
        TripStatusEnum.ARRIVED,
        TripStatusEnum.PICKED_UP,
        TripStatusEnum.IN_PROGRESS
    ]

    trip = db.execute(
        select(Trip)
        .where(
            Trip.rider_id == session.user_id,
            Trip.status.in_(active_statuses)
        )
        .order_by(Trip.created_on.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not trip:
        return {"trip": None}

    return {
        "trip": {
            "trip_id": trip.trip_id,
            "status": trip.status.value,

            "pickup_address": trip.pickup_address,
            "drop_address": trip.drop_address,

            "pickup_lat": trip.pickup_lat,
            "pickup_lng": trip.pickup_lng,
            "drop_lat": trip.drop_lat,
            "drop_lng": trip.drop_lng,

            "vehicle_category": trip.vehicle_category,
            "fare_amount": trip.fare_amount,

            "driver_id": trip.driver_id,
            "vehicle_id": trip.vehicle_id,

            "requested_at": trip.requested_at,
            "assigned_at": trip.assigned_at,
            "picked_up_at": trip.picked_up_at
        }
    }


@router.post(
    "/nearby-10km",
    response_model=NearbyDriversListResponse
)
def get_nearby_drivers_10km(
    payload: NearbyDriversRequest,
    db: Session = Depends(get_db)
):
    rows = get_online_drivers_within_10km(
        db,
        city_id=payload.city_id,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng
    )

    drivers = [
        NearbyDriverResponse(
            driver_id=r[0],
            tenant_id=r[1],
            latitude=r[2],
            longitude=r[3],
            vehicle_category=r[4]
        )
        for r in rows
    ]

    return NearbyDriversListResponse(drivers=drivers)