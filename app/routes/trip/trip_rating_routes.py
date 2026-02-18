from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role

from app.models.trip import Trip
from app.models.trip.trip_rating import TripRating
from app.models.common.user_session import UserSession

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.schemas.trip import (
    TripRatingCreateRequest,
    TripRatingResponse
)

from app.services.trip.rating_service import update_driver_avg_rating

router = APIRouter(
    prefix="/trips",
    tags=["Trip Ratings"]
)

@router.post(
    "/{trip_id}/rate",
    response_model=TripRatingResponse
)
def rate_trip(
    trip_id: int,
    payload: TripRatingCreateRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(TenantRoleEnum.RIDER)
    )
):
    trip = db.execute(
        select(Trip).where(Trip.trip_id == trip_id)
    ).scalar_one_or_none()

    if not trip:
        raise HTTPException(404, "Trip not found")

    if trip.rider_id != session.user_id:
        raise HTTPException(403, "Not your trip")

    if trip.status != TripStatusEnum.COMPLETED:
        raise HTTPException(400, "Trip not completed yet")

    if not trip.driver_id:
        raise HTTPException(400, "Driver not assigned")

    # Prevent duplicate rating
    existing = db.execute(
        select(TripRating).where(
            TripRating.trip_id == trip_id,
            TripRating.rater_id == session.user_id
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(400, "Trip already rated")

    rating = TripRating(
        trip_id=trip_id,
        rater_id=session.user_id,
        ratee_id=trip.driver_id,
        rating=payload.rating,
        comment=payload.comment
    )

    db.add(rating)

    #  Update driver average rating
    update_driver_avg_rating(db, trip.driver_id)

    db.commit()
    db.refresh(rating)

    return rating


@router.get(
    "/{trip_id}/rating",
    response_model=TripRatingResponse
)
def get_trip_rating(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_db)  # any logged user
):
    rating = db.execute(
        select(TripRating).where(
            TripRating.trip_id == trip_id
        )
    ).scalar_one_or_none()

    if not rating:
        raise HTTPException(404, "Rating not found")

    return rating
