from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from starlette import status
from datetime import datetime, time, timezone, timedelta

from app.core.database import get_db

from app.models.trip.trip import Trip
from app.models.common.user import AppUser
from app.models.driver.driver_shift import DriverShift
from app.models.driver.driver_location import DriverLocation
from app.models.driver.driver_location_history import DriverLocationHistory
from app.models.driver.driver_vehicle_assignment import DriverVehicleAssignment

from app.schemas.driver import (
    StartDriverShiftRequest,
    EndDriverShiftRequest,
    DriverShiftResponse,
    UpdateDriverLocationRequest,
    DriverLocationResponse
)
from app.schemas.enums import DriverShiftStatusEnum, TripStatusEnum

from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum
from app.models.common.user_session import UserSession


router = APIRouter(prefix="/drivers", tags=["Driver Shift & Location"])


# Time helpers

def compute_expected_end_at(
    start_time: time,
    end_time: time,
    now: datetime
) -> datetime:
    """
    Convert assignment TIME into today's TIMESTAMPTZ.
    Handles overnight shifts automatically.
    """
    today = now.date()
    end_dt = datetime.combine(today, end_time, tzinfo=now.tzinfo)

    # Overnight shift (e.g. 22:00 to 06:00)
    if end_time <= start_time:
        end_dt += timedelta(days=1)

    return end_dt


def is_now_within_assignment(
    start_time: time,
    end_time: time,
    now_time: time
) -> bool:
    """
    Check if current time falls inside a DAILY assignment window.
    Handles overnight shifts.
    """
    if start_time <= end_time:
        return start_time <= now_time <= end_time
    else:
        # Overnight window
        return now_time >= start_time or now_time <= end_time


# Auto end shift if expected_end_at passed
def auto_end_shift_if_required(
    db: Session,
    shift: DriverShift,
    now: datetime
) -> bool:
    if (
        shift.status == DriverShiftStatusEnum.ONLINE
        and shift.ended_at is None
        and shift.expected_end_at is not None
        and now >= shift.expected_end_at
    ):
        shift.status = DriverShiftStatusEnum.OFFLINE
        shift.ended_at = shift.expected_end_at
        db.commit()
        return True
    return False


# 1) Start shift (go ONLINE)
@router.post(
    "/shifts/start",
    response_model=DriverShiftResponse,
    status_code=status.HTTP_201_CREATED
)
def start_driver_shift(
    payload: StartDriverShiftRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    # Enforce ownership
    if payload.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized driver")

    driver = db.execute(
        select(AppUser).where(AppUser.user_id == session.user_id)
    ).scalar_one_or_none()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Prevent multiple online shifts
    existing = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == payload.driver_id,
                DriverShift.status == DriverShiftStatusEnum.ONLINE,
                DriverShift.ended_at.is_(None)
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Driver already ONLINE")

    now = datetime.now(timezone.utc)
    now_time = now.time()

    # Find valid DAILY assignment
    assignments = db.execute(
        select(DriverVehicleAssignment).where(
            DriverVehicleAssignment.driver_id == payload.driver_id
        )
    ).scalars().all()

    assignment = None
    for a in assignments:
        if is_now_within_assignment(a.start_time, a.end_time, now_time):
            assignment = a
            break

    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="No active vehicle assignment for current time window"
        )

    # Compute expected_end_at TIMESTAMPTZ
    expected_end_at = compute_expected_end_at(
        assignment.start_time,
        assignment.end_time,
        now
    )

    # Create shift
    shift = DriverShift(
        driver_id=payload.driver_id,
        tenant_id=payload.tenant_id,
        vehicle_id=assignment.vehicle_id,
        status=DriverShiftStatusEnum.ONLINE,
        started_at=now,
        expected_end_at=expected_end_at,
        last_latitude=payload.latitude,
        last_longitude=payload.longitude
    )

    db.add(shift)

    # Upsert driver_location
    loc = db.execute(
        select(DriverLocation).where(
            DriverLocation.driver_id == payload.driver_id
        )
    ).scalar_one_or_none()

    if loc:
        loc.latitude = payload.latitude
        loc.longitude = payload.longitude
        loc.last_updated = now
    else:
        db.add(DriverLocation(
            driver_id=payload.driver_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            last_updated=now
        ))

    # Location history
    db.add(DriverLocationHistory(
        driver_id=payload.driver_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        recorded_at=now
    ))

    db.commit()
    db.refresh(shift)
    return shift


# 2) Update location
@router.post(
    "/location/update",
    response_model=DriverLocationResponse,
    status_code=status.HTTP_200_OK
)
def update_driver_location(
    payload: UpdateDriverLocationRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    if payload.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized driver")

    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == session.user_id,
                DriverShift.status != DriverShiftStatusEnum.OFFLINE,
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=400,
            detail="Driver is not ONLINE"
        )

    # Auto end shift if required
    active_trip = db.execute(
        select(Trip).where(
            and_(
                Trip.driver_id == session.user_id,
                Trip.status.in_([TripStatusEnum.ASSIGNED, TripStatusEnum.PICKED_UP])
            )
        )
    ).first()

    # Only run auto-end logic if the driver is NOT on a trip
    if not active_trip:
        if auto_end_shift_if_required(db, shift, datetime.now(timezone.utc)):
             raise HTTPException(status_code=400, detail="Shift automatically ended due to time limit")
    # Update location
    loc = db.execute(
        select(DriverLocation).where(
            DriverLocation.driver_id == payload.driver_id
        )
    ).scalar_one_or_none()

    if loc:
        loc.latitude = payload.latitude
        loc.longitude = payload.longitude
        loc.last_updated = now
    else:
        loc = DriverLocation(
            driver_id=payload.driver_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            last_updated=now
        )
        db.add(loc)

    db.add(DriverLocationHistory(
        driver_id=payload.driver_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        recorded_at=now
    ))

    shift.last_latitude = payload.latitude
    shift.last_longitude = payload.longitude


    db.commit()
    db.refresh(loc)
    return loc


# 3) End shift manually
@router.post(
    "/shifts/end",
    status_code=status.HTTP_200_OK
)
def end_driver_shift(
    payload: EndDriverShiftRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    if payload.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized driver")

    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == session.user_id,
                DriverShift.status == DriverShiftStatusEnum.ONLINE,
                DriverShift.ended_at.is_(None)
            )
        )
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=404,
            detail="No active shift found"
        )

    shift.status = DriverShiftStatusEnum.OFFLINE
    shift.ended_at = now

    db.commit()
    return {"message": "Shift ended successfully"}


# 4) Get current shift
@router.get(
    "/shift/current",
    response_model=DriverShiftResponse
)
def get_current_driver_shift(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == session.user_id,
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=404, detail="No active shift")

    auto_end_shift_if_required(db, shift, now)
    return shift

