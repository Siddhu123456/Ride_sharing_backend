from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, select, and_

from app.models.trip import Trip
from app.models.driver_shift import DriverShift
from app.schemas.enums import TripStatusEnum


def set_driver_shift_online(db: Session, driver_id: int):
    shift = db.execute(
        select(DriverShift)
        .where(
            and_(
                DriverShift.driver_id == driver_id,
                DriverShift.ended_at.is_(None)
            )
        )
        .order_by(desc(DriverShift.started_at))
        .limit(1)
    ).scalar_one_or_none()

    if shift:
        shift.status = "ONLINE"
        db.flush()


def set_driver_shift_on_trip(db: Session, driver_id: int):
    shift = db.execute(
        select(DriverShift)
        .where(
            and_(
                DriverShift.driver_id == driver_id,
                DriverShift.ended_at.is_(None)
            )
        )
        .order_by(desc(DriverShift.started_at))
        .limit(1)
    ).scalar_one_or_none()

    if shift:
        shift.status = "ON_TRIP"
        db.flush()



def cancel_trip(db: Session, trip: Trip, cancelled_by_user_id: int):
    trip.status = TripStatusEnum.CANCELLED
    trip.cancelled_at = datetime.now(timezone.utc)
    trip.updated_by = cancelled_by_user_id
    trip.updated_on = datetime.now(timezone.utc)

    # Driver goes back ONLINE if already assigned
    if trip.driver_id:
        set_driver_shift_online(db, trip.driver_id)

    db.flush()

