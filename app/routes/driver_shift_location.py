from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from starlette import status
from datetime import datetime, time, timezone, timedelta

from app.core.database import get_db

from app.models.user import AppUser
from app.models.driver_shift import DriverShift
from app.models.driver_location import DriverLocation
from app.models.driver_location_history import DriverLocationHistory
from app.models.driver_vehicle_assignment import DriverVehicleAssignment

from app.schemas.driver_shift import (
    StartDriverShiftRequest,
    EndDriverShiftRequest,
    DriverShiftResponse
)
from app.schemas.driver_location import (
    UpdateDriverLocationRequest,
    DriverLocationResponse
)
from app.schemas.enums import DriverShiftStatusEnum

router = APIRouter(prefix="/drivers", tags=["Driver Shift & Location"])


# =========================================================
# 🔧 TIME HELPERS
# =========================================================

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

    # Overnight shift (e.g. 22:00 → 06:00)
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


# =========================================================
# ✅ Auto end shift if expected_end_at passed
# =========================================================
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


# =========================================================
# ✅ 1) Start Shift (Go ONLINE)
# =========================================================
@router.post(
    "/shifts/start",
    response_model=DriverShiftResponse,
    status_code=status.HTTP_201_CREATED
)
def start_driver_shift(
    payload: StartDriverShiftRequest,
    db: Session = Depends(get_db)
):
    # Validate driver
    driver = db.execute(
        select(AppUser).where(AppUser.user_id == payload.driver_id)
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


# =========================================================
# ✅ 2) Update Location
# =========================================================
@router.post(
    "/location/update",
    response_model=DriverLocationResponse,
    status_code=status.HTTP_200_OK
)
def update_driver_location(
    payload: UpdateDriverLocationRequest,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == payload.driver_id,
                DriverShift.status == DriverShiftStatusEnum.ONLINE,
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=400,
            detail="Driver is not ONLINE"
        )

    # Auto end shift
    if auto_end_shift_if_required(db, shift, now):
        raise HTTPException(
            status_code=400,
            detail="Shift automatically ended"
        )

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


# =========================================================
# ✅ 3) End Shift Manually
# =========================================================
@router.post(
    "/shifts/end",
    status_code=status.HTTP_200_OK
)
def end_driver_shift(
    payload: EndDriverShiftRequest,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == payload.driver_id,
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


# =========================================================
# ✅ 4) Get Current Shift
# =========================================================
@router.get(
    "/{driver_id}/shift/current",
    response_model=DriverShiftResponse
)
def get_current_driver_shift(
    driver_id: int,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == driver_id,
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=404, detail="No active shift")

    auto_end_shift_if_required(db, shift, now)
    return shift
