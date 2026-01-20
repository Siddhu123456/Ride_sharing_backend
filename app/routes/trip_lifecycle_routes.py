from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.user_session import UserSession
from app.models.trip import Trip

from app.schemas.trip_lifecycle import TripCancelRequest, TripCompleteRequest, TripStatusResponse
from app.services.trip_lifecycle_service import cancel_trip, set_driver_shift_online
from app.services.fare_service import compute_fare_simple, insert_fare_breakdown
from app.services.payment_service import create_payment_for_trip


router = APIRouter(prefix="/trips", tags=["Trips - Lifecycle"])


# ✅ Rider polls trip status
@router.get("/{trip_id}", response_model=TripStatusResponse)
def get_trip_status(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_db)  # don't force role (any logged in user can check)
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()
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


# ✅ Rider cancels trip (only if not PICKED_UP/COMPLETED)
@router.post("/{trip_id}/cancel", status_code=status.HTTP_200_OK)
def rider_cancel_trip(
    trip_id: int,
    payload: TripCancelRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.rider_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status in [TripStatusEnum.PICKED_UP, TripStatusEnum.COMPLETED]:
        raise HTTPException(status_code=400, detail="Cannot cancel after pickup")

    cancel_trip(db, trip, cancelled_by_user_id=session.user_id)
    db.commit()

    return {"message": "Trip cancelled successfully"}


# ✅ Driver completes trip (only if PICKED_UP)
@router.post("/{trip_id}/complete", status_code=status.HTTP_200_OK)
def driver_complete_trip(
    trip_id: int,
    payload: TripCompleteRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatusEnum.PICKED_UP:
        raise HTTPException(status_code=400, detail="Trip can be completed only after PICKED_UP")

    # ✅ compute fare + insert breakdown
    fare_data = compute_fare_simple(trip, payload.distance_km, payload.duration_minutes)
    insert_fare_breakdown(db, trip.trip_id, fare_data)

    trip.fare_amount = fare_data["final_fare"]
    trip.status = TripStatusEnum.COMPLETED
    trip.completed_at = datetime.now(timezone.utc)
    trip.updated_by = session.user_id
    trip.updated_on = datetime.now(timezone.utc)

    # ✅ create payment row (PENDING)
    create_payment_for_trip(db, trip)

    # ✅ set driver back ONLINE
    set_driver_shift_online(db, session.user_id)

    db.commit()
    return {"message": "Trip completed successfully", "fare": fare_data["final_fare"]}
