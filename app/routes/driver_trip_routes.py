from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession
from app.models.trip import Trip
from app.schemas.driver_trip import ActiveTripResponse
from app.schemas.enums import TripStatusEnum

router = APIRouter(prefix="/driver/trips", tags=["Driver - Trips"])


@router.get("/active", response_model=ActiveTripResponse | None)
def get_active_trip(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    trip = db.execute(
        select(Trip).where(
            Trip.driver_id == session.user_id,
            Trip.status.in_([
                TripStatusEnum.ASSIGNED,
                TripStatusEnum.PICKED_UP
            ])
        )
    ).scalar_one_or_none()

    return trip
