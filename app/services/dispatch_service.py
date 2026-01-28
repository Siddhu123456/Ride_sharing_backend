from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.trip import Trip
from app.models.core import City
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
# ✅ Find eligible drivers for a trip
# =========================================================
def find_eligible_driver_ids(db: Session, trip: Trip) -> list[int]:
    stmt = (
        select(DriverShift.driver_id)
        .join(DriverProfile, DriverProfile.driver_id == DriverShift.driver_id)
        .join(
            DriverVehicleAssignment,
            and_(
                DriverVehicleAssignment.driver_id == DriverShift.driver_id,
                DriverVehicleAssignment.is_active.is_(True),
            )
        )
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .join(City, City.city_id == trip.city_id)
        .where(
            DriverShift.tenant_id == trip.tenant_id,
            DriverShift.status == "ONLINE",
            DriverShift.ended_at.is_(None),

            DriverProfile.approval_status == ApprovalStatusEnum.APPROVED,

            Vehicle.approval_status == ApprovalStatusEnum.APPROVED,
            Vehicle.status == VehicleStatusEnum.ACTIVE,
            Vehicle.category == trip.vehicle_category,

            # ✅ PostGIS city containment check
            func.ST_Contains(
                City.boundary,
                func.ST_SetSRID(
                    func.ST_Point(
                        DriverShift.last_longitude,
                        DriverShift.last_latitude
                    ),
                    4326
                )
            )
        )
        .distinct()
    )

    return db.execute(stmt).scalars().all()


# =========================================================
# ✅ Create first dispatch attempt
# =========================================================
def create_first_offer(
    db: Session,
    trip: Trip,
    created_by: int
) -> DispatchAttempt | None:
    driver_ids = find_eligible_driver_ids(db, trip)

    if not driver_ids:
        return None

    attempt = DispatchAttempt(
        trip_id=trip.trip_id,
        driver_id=driver_ids[0],
        created_by=created_by
    )

    db.add(attempt)
    db.flush()
    return attempt


# =========================================================
# ✅ Send next driver offer
# =========================================================
def send_next_offer(
    db: Session,
    trip: Trip,
    created_by: int
) -> DispatchAttempt | None:
    eligible_driver_ids = find_eligible_driver_ids(db, trip)

    if not eligible_driver_ids:
        return None

    already_offered = db.execute(
        select(DispatchAttempt.driver_id)
        .where(DispatchAttempt.trip_id == trip.trip_id)
    ).scalars().all()

    for driver_id in eligible_driver_ids:
        if driver_id in already_offered:
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
# ✅ Assign trip after ACCEPT
# =========================================================
def assign_trip(
    db: Session,
    trip: Trip,
    driver_id: int,
    updated_by: int
):
    now = datetime.now(timezone.utc)

    assignment = db.execute(
        select(DriverVehicleAssignment)
        .where(
            and_(
                DriverVehicleAssignment.driver_id == driver_id,
                DriverVehicleAssignment.is_active.is_(True)
            )
        )
    ).scalar_one_or_none()

    if not assignment:
        raise ValueError("Driver has no active vehicle assignment")

    trip.driver_id = driver_id
    trip.vehicle_id = assignment.vehicle_id
    trip.status = TripStatusEnum.ASSIGNED
    trip.assigned_at = now
    trip.updated_by = updated_by
    trip.updated_on = now

    shift = db.execute(
        select(DriverShift)
        .where(
            DriverShift.driver_id == driver_id,
            DriverShift.ended_at.is_(None)
        )
    ).scalar_one_or_none()

    if shift:
        shift.status = "ON_TRIP"
        shift.vehicle_id = assignment.vehicle_id
