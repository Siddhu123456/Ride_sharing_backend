from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.trip import Trip
from app.models.driver_shift import DriverShift
from app.models.user_session import UserSession

from app.schemas.trip_lifecycle import (
    TripCancelRequest,
    TripCompleteRequest,
    TripStatusResponse
)
from app.services.trip_lifecycle_service import cancel_trip
from app.services.payment_service import create_payment_for_trip

router = APIRouter(prefix="/trips", tags=["Trips - Lifecycle"])

@router.get("/{trip_id}", response_model=TripStatusResponse)
def get_trip_status(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_db)  # any logged-in user
):
    trip = db.execute(
        select(Trip).where(Trip.trip_id == trip_id)
    ).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return TripStatusResponse(
        trip_id=trip.trip_id,
        status=trip.status,
        driver_id=trip.driver_id,
        vehicle_id=trip.vehicle_id,
        requested_at=trip.requested_at,
        assigned_at=trip.assigned_at,
        picked_up_at=trip.picked_up_at,
        completed_at=trip.completed_at,
        cancelled_at=trip.cancelled_at,
    )


@router.post("/{trip_id}/cancel")
def cancel_trip_route(
    trip_id: int,
    payload: TripCancelRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    trip = db.execute(
        select(Trip).where(Trip.trip_id == trip_id)
    ).scalar_one_or_none()

    if not trip or trip.rider_id != session.user_id:
        raise HTTPException(404, "Trip not found")

    if trip.status not in [
        TripStatusEnum.REQUESTED,
        TripStatusEnum.ASSIGNED
    ]:
        raise HTTPException(400, "Cannot cancel now")

    cancel_trip(db, trip, session.user_id)
    db.commit()

    return {"message": "Trip cancelled"}


@router.post("/{trip_id}/complete")
def complete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()

    if not trip or trip.driver_id != session.user_id:
        raise HTTPException(404, "Trip not found")

    if trip.status != TripStatusEnum.PICKED_UP:
        raise HTTPException(400, "Invalid trip state")

    trip.status = TripStatusEnum.COMPLETED
    trip.completed_at = datetime.now(timezone.utc)

    # ✅ Payment uses stored fare_amount
    create_payment_for_trip(db, trip)

    db.commit()
    return {"fare": trip.fare_amount}
