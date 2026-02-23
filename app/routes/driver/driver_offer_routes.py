from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.common.user_session import UserSession
from app.models.trip.trip import Trip
from app.models.trip.dispatch_attempt import DispatchAttempt

from app.services.trip.distance_service import calculate_distance_km

from app.schemas.driver import DriverOfferResponse, DriverOfferRespondRequest
from app.services.trip.dispatch_service import send_next_offer, assign_trip

router = APIRouter(prefix="/driver/offers", tags=["Driver Offers - Phase 2"])


# Driver views pending offers
@router.get("/pending", response_model=list[DriverOfferResponse])
def pending_offers(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    rows = db.execute(
        select(
            DispatchAttempt.attempt_id,
            DispatchAttempt.sent_at,

            Trip.trip_id,
            Trip.pickup_lat,
            Trip.pickup_lng,
            Trip.pickup_address,
            Trip.drop_lat,
            Trip.drop_lng,
            Trip.drop_address,
            Trip.fare_amount
        )
        .join(Trip, Trip.trip_id == DispatchAttempt.trip_id)
        .where(
            and_(
                DispatchAttempt.driver_id == session.user_id,
                DispatchAttempt.response.is_(None),
                Trip.status == TripStatusEnum.REQUESTED
            )
        )
        .order_by(DispatchAttempt.sent_at.asc())
    ).all()

    offers = []

    for row in rows:
        distance_km = calculate_distance_km(
            row.pickup_lat,
            row.pickup_lng,
            row.drop_lat,
            row.drop_lng
        )

        offers.append(
            DriverOfferResponse(
                attempt_id=row.attempt_id,
                trip_id=row.trip_id,

                pickup_lat=row.pickup_lat,
                pickup_lng=row.pickup_lng,
                pickup_address=row.pickup_address,

                drop_lat=row.drop_lat,
                drop_lng=row.drop_lng,
                drop_address=row.drop_address,

                distance_km=round(distance_km, 2),  # Distance in kilometers (rounded)
                fare_amount=row.fare_amount,

                sent_at=row.sent_at
            )
        )

    return offers




@router.post("/{attempt_id}/respond", status_code=status.HTTP_200_OK)
def respond_offer(
    attempt_id: int,
    payload: DriverOfferRespondRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):

    attempt = db.execute(
        select(DispatchAttempt).where(DispatchAttempt.attempt_id == attempt_id)
    ).scalar_one_or_none()

    if not attempt:
        raise HTTPException(status_code=404, detail="Offer not found")

    if attempt.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your offer")

    # Already responded?
    if attempt.response is not None:
        raise HTTPException(status_code=400, detail="Offer already responded")

    trip = db.execute(
        select(Trip)
        .where(Trip.trip_id == attempt.trip_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now = datetime.now(timezone.utc)

    attempt.responded_at = now
    attempt.updated_by = session.user_id
    attempt.updated_on = now
    
    # ACCEPT FLOW
    if payload.accept:

        # Someone else already accepted?
        if trip.driver_id is not None:
            attempt.response = "FAILED_ALREADY_ASSIGNED"
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="Trip already assigned to another driver"
            )

        attempt.response = "ACCEPTED"

        try:
            assign_trip(
                db,
                trip_id=trip.trip_id,
                driver_id=session.user_id,
                updated_by=session.user_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Cancel ALL other pending attempts
        db.query(DispatchAttempt).filter(
            DispatchAttempt.trip_id == trip.trip_id,
            DispatchAttempt.attempt_id != attempt_id,
            DispatchAttempt.response.is_(None)
        ).update(
            {"response": "CANCELLED", "responded_at": now},
            synchronize_session=False
        )

        db.commit()
        db.refresh(trip)

        return {
            "trip": {
                "trip_id": trip.trip_id,
                "status": trip.status.value,

                "pickup_lat": trip.pickup_lat,
                "pickup_lng": trip.pickup_lng,
                "pickup_address": trip.pickup_address,

                "drop_lat": trip.drop_lat,
                "drop_lng": trip.drop_lng,
                "drop_address": trip.drop_address,

                "fare_amount": trip.fare_amount
            }
        }

    # REJECT FLOW
    attempt.response = "REJECTED"

    # Are there still pending offers?
    pending_exists = db.query(DispatchAttempt).filter(
        DispatchAttempt.trip_id == trip.trip_id,
        DispatchAttempt.response.is_(None)
    ).count() > 0

    next_offer = None

    if not pending_exists:
        # No pending → advance dispatch
        next_offer = send_next_offer(db, trip, created_by=session.user_id)

    db.commit()

    if next_offer:
        return {"message": "Offer rejected. Next driver notified."}

    return {"message": "Offer rejected."}
