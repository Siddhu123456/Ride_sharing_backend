from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role
from app.models.trip.dispatch_attempt import DispatchAttempt
from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.trip.trip import Trip
from app.models.driver.driver_shift import DriverShift
from app.models.common.user_session import UserSession

from app.schemas.trip import (
    TripCancelRequest,
    TripCompleteRequest,
    TripStatusResponse
)
from app.services.trip.trip_lifecycle_service import cancel_trip, set_driver_shift_online
from app.services.trip.payment_service import create_payment_for_trip

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

    now = datetime.now(timezone.utc)

    # If trip was ASSIGNED → set driver OFFLINE
    if trip.status == TripStatusEnum.ASSIGNED and trip.driver_id:

        driver_shift = db.execute(
            select(DriverShift)
            .where(
                DriverShift.driver_id == trip.driver_id,
                DriverShift.status == "ON_TRIP",
                DriverShift.ended_at.is_(None)
            )
        ).scalar_one_or_none()

        if driver_shift:
            driver_shift.status = "ONLINE"

    # CANCEL TRIP
    trip.status = TripStatusEnum.CANCELLED
    trip.cancelled_at = now
    trip.updated_by = session.user_id
    trip.updated_on = now

    # VOID DISPATCH ATTEMPTS
    db.query(DispatchAttempt).filter(
        DispatchAttempt.trip_id == trip.trip_id,
        DispatchAttempt.response.is_(None)
    ).update(
        {
            "response": "CANCELLED_BY_RIDER",
            "responded_at": now
        },
        synchronize_session=False
    )

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

    set_driver_shift_online(db,session.user_id)
    create_payment_for_trip(db, trip)

    db.commit()
    return {"fare": trip.fare_amount}
