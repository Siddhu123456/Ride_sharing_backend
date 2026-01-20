from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.trip import Trip
from app.models.dispatch_attempt import DispatchAttempt

from app.models.driver_shift import DriverShift
from app.models.driver_profile import DriverProfile
from app.models.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.vehicle import Vehicle

from app.schemas.enums import (
    ApprovalStatusEnum,
    VehicleStatusEnum,
    TripStatusEnum
)


# =========================================================
# ✅ Find eligible drivers for a trip (NO distance restriction)
# Supports TIMED assignments: start_time <= now <= end_time
# =========================================================
def find_eligible_driver_ids(db: Session, trip: Trip) -> list[int]:
    now = datetime.now(timezone.utc)

    stmt = (
        select(DriverShift.driver_id)
        .join(DriverProfile, DriverProfile.driver_id == DriverShift.driver_id)
        .join(
            DriverVehicleAssignment,
            and_(
                DriverVehicleAssignment.driver_id == DriverShift.driver_id,
                DriverVehicleAssignment.start_time <= now,
                or_(
                    DriverVehicleAssignment.end_time.is_(None),
                    DriverVehicleAssignment.end_time >= now
                )
            )
        )
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .where(
            DriverShift.tenant_id == trip.tenant_id,
            DriverShift.ended_at.is_(None),
            DriverShift.status == "ONLINE",

            DriverProfile.approval_status == ApprovalStatusEnum.APPROVED,

            Vehicle.approval_status == ApprovalStatusEnum.APPROVED,
            Vehicle.status == VehicleStatusEnum.ACTIVE,

            Vehicle.category == trip.vehicle_category,
        )
        .distinct()
    )

    return db.execute(stmt).scalars().all()


# =========================================================
# ✅ Create first dispatch offer
# =========================================================
def create_first_offer(db: Session, trip: Trip, created_by: int) -> DispatchAttempt | None:
    driver_ids = find_eligible_driver_ids(db, trip)

    if not driver_ids:
        return None

    chosen_driver_id = driver_ids[0]

    attempt = DispatchAttempt(
        trip_id=trip.trip_id,
        driver_id=chosen_driver_id,
        created_by=created_by
    )

    db.add(attempt)
    db.flush()
    return attempt


# =========================================================
# ✅ Send offer to next eligible driver (avoid repeats)
# =========================================================
def send_next_offer(db: Session, trip: Trip, created_by: int) -> DispatchAttempt | None:
    eligible_driver_ids = find_eligible_driver_ids(db, trip)

    if not eligible_driver_ids:
        return None

    already_offered_driver_ids = db.execute(
        select(DispatchAttempt.driver_id).where(DispatchAttempt.trip_id == trip.trip_id)
    ).scalars().all()

    for driver_id in eligible_driver_ids:
        if driver_id in already_offered_driver_ids:
            continue

        attempt = DispatchAttempt(
            trip_id=trip.trip_id,
            driver_id=driver_id,
            created_by=created_by
        )
        db.add(attempt)
        db.flush()
        return attempt

    return None


# =========================================================
# ✅ Assign trip to driver after ACCEPT
# Supports TIMED assignments: start_time <= now <= end_time
# =========================================================
def assign_trip(db: Session, trip: Trip, driver_id: int, updated_by: int):
    now = datetime.now(timezone.utc)

    # ✅ pick current active assignment for driver
    assignment = db.execute(
        select(DriverVehicleAssignment).where(
            and_(
                DriverVehicleAssignment.driver_id == driver_id,
                DriverVehicleAssignment.start_time <= now,
                or_(
                    DriverVehicleAssignment.end_time.is_(None),
                    DriverVehicleAssignment.end_time >= now
                )
            )
        ).order_by(DriverVehicleAssignment.start_time.desc())
    ).scalar_one_or_none()

    if not assignment:
        raise ValueError("Driver has no active vehicle assignment currently")

    # ✅ update trip
    trip.driver_id = driver_id
    trip.vehicle_id = assignment.vehicle_id
    trip.status = TripStatusEnum.ASSIGNED
    trip.assigned_at = now
    trip.updated_by = updated_by
    trip.updated_on = now

    # ✅ update driver shift -> ON_TRIP
    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == driver_id,
                DriverShift.ended_at.is_(None)
            )
        )
    ).scalar_one_or_none()

    if shift:
        shift.status = "ON_TRIP"
        shift.vehicle_id = assignment.vehicle_id
