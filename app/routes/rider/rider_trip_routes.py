from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.trip.trip import Trip
from app.models.common.user_session import UserSession

from app.services.trip.geo_coding_service import reverse_geocode

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

            "pickup_address": reverse_geocode(trip.pickup_lat, trip.pickup_lng),
            "drop_address": reverse_geocode(trip.drop_lat, trip.drop_lng),

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
