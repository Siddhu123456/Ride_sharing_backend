from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
import math

from app.models.trip.trip import Trip
from app.models.trip.dispatch_attempt import DispatchAttempt
from app.models.driver.driver_shift import DriverShift
from app.models.driver.driver_profile import DriverProfile
from app.models.driver.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.fleet_owner.vehicle import Vehicle

from app.schemas.enums import (
    ApprovalStatusEnum,
    VehicleStatusEnum,
    TripStatusEnum
)

# CONFIG

BATCH_SIZE = 3
INITIAL_RADIUS_KM = 2
RADIUS_INCREMENT_KM = 2
MAX_RADIUS_KM = 10



# HAVERSINE DISTANCE

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# FIND ELIGIBLE DRIVERS

def find_eligible_drivers(db: Session, trip: Trip, radius_km: float):

    rows = db.execute(
        select(
            DriverShift.driver_id,
            DriverShift.last_latitude,
            DriverShift.last_longitude
        )
        .join(DriverProfile, DriverProfile.driver_id == DriverShift.driver_id)
        .join(
            DriverVehicleAssignment,
            and_(
                DriverVehicleAssignment.driver_id == DriverShift.driver_id,
                DriverVehicleAssignment.is_active.is_(True),
            )
        )
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .where(
            DriverShift.tenant_id == trip.tenant_id,
            DriverShift.status == "ONLINE",
            DriverShift.ended_at.is_(None),

            DriverProfile.approval_status == ApprovalStatusEnum.APPROVED,

            Vehicle.approval_status == ApprovalStatusEnum.APPROVED,
            Vehicle.status == VehicleStatusEnum.ACTIVE,
            Vehicle.category == trip.vehicle_category
        )
    ).all()

    eligible = []

    for driver_id, lat, lng in rows:

        distance = haversine_km(
            float(trip.pickup_lat),
            float(trip.pickup_lng),
            float(lat),
            float(lng)
        )

        if distance <= radius_km:
            eligible.append((driver_id, distance))

    eligible.sort(key=lambda x: x[1])
    return [d[0] for d in eligible]


# DISPATCH TRIP — EXPANDING SEARCH

def dispatch_trip(db: Session, trip: Trip, created_by: int) -> bool:

    radius = INITIAL_RADIUS_KM

    while radius <= MAX_RADIUS_KM:

        eligible = find_eligible_drivers(db, trip, radius)

        if eligible:
            batch = eligible[:BATCH_SIZE]

            for driver_id in batch:
                db.add(DispatchAttempt(
                    trip_id=trip.trip_id,
                    driver_id=driver_id,
                    created_by=created_by,
                    response=None
                ))

            db.commit()
            print(f"✅ Dispatch created with radius {radius} km")
            return True

        print(f" No drivers within {radius} km — expanding radius")
        radius += RADIUS_INCREMENT_KM

    print(" No drivers found within max radius")
    return False


# NEXT WAVE

def send_next_offer(db: Session, trip: Trip, created_by: int):

    if trip.driver_id is not None:
        return None

    attempted_ids = [
        r[0] for r in db.query(DispatchAttempt.driver_id)
        .filter(DispatchAttempt.trip_id == trip.trip_id)
        .all()
    ]

    radius = INITIAL_RADIUS_KM

    while radius <= MAX_RADIUS_KM:

        eligible = find_eligible_drivers(db, trip, radius)

        # Remove already attempted drivers
        eligible = [d for d in eligible if d not in attempted_ids]

        if eligible:
            batch = eligible[:BATCH_SIZE]

            attempts = []

            for driver_id in batch:
                attempt = DispatchAttempt(
                    trip_id=trip.trip_id,
                    driver_id=driver_id,
                    created_by=created_by,
                    response=None
                )
                db.add(attempt)
                attempts.append(attempt)

            db.commit()
            print(f"✅ Next wave sent at radius {radius} km")
            return attempts[0]

        radius += RADIUS_INCREMENT_KM

    trip.status = TripStatusEnum.CANCELLED
    db.commit()
    print("Trip cancelled — no drivers available")
    return None


# ASSIGN DRIVER

def assign_trip(db: Session, trip_id: int, driver_id: int, updated_by: int):

    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()

    if not trip:
        raise ValueError("Trip not found")

    if trip.driver_id is not None:
        raise ValueError("Trip already assigned")

    now = datetime.now(timezone.utc)

    assignment = db.execute(
        select(DriverVehicleAssignment)
        .where(
            DriverVehicleAssignment.driver_id == driver_id,
            DriverVehicleAssignment.is_active.is_(True)
        )
    ).scalar_one()

    trip.driver_id = driver_id
    trip.vehicle_id = assignment.vehicle_id
    trip.status = TripStatusEnum.ASSIGNED
    trip.assigned_at = now
    trip.updated_by = updated_by
    trip.updated_on = now

    # Cancel other offers
    db.query(DispatchAttempt).filter(
        DispatchAttempt.trip_id == trip_id,
        DispatchAttempt.driver_id != driver_id,
        DispatchAttempt.response.is_(None)
    ).update(
        {"response": "CANCELLED", "responded_at": now},
        synchronize_session=False
    )

    shift = db.query(DriverShift).filter(
        DriverShift.driver_id == driver_id,
        DriverShift.ended_at.is_(None)
    ).first()

    if shift:
        shift.status = "ON_TRIP"
        shift.vehicle_id = assignment.vehicle_id

    db.commit()
