from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from starlette import status
from datetime import datetime, timezone

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

router = APIRouter(prefix="/drivers", tags=["Driver Shift & Location"])


# =========================================================
# ✅ Helper: Auto end shift if expected_end_at is passed
# =========================================================
def auto_end_shift_if_required(db: Session, shift: DriverShift, now: datetime):
    if shift and shift.status == "ONLINE" and shift.ended_at is None:
        if shift.expected_end_at is not None and now >= shift.expected_end_at:
            shift.status = "OFFLINE"
            shift.ended_at = shift.expected_end_at
            db.commit()
            db.refresh(shift)
            return True
    return False


# =========================================================
# ✅ 1) Start Shift (Go ONLINE)
# Rules:
# - Must have valid assignment window for NOW
# - start_time <= now <= end_time
# - Shift expected_end_at = assignment.end_time
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
    driver = db.execute(
        select(AppUser).where(AppUser.user_id == payload.driver_id)
    ).scalar_one_or_none()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # ✅ prevent multiple online shifts
    existing_online = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == payload.driver_id,
                DriverShift.status == "ONLINE",
                DriverShift.ended_at.is_(None)
            )
        )
    ).scalar_one_or_none()

    if existing_online:
        raise HTTPException(status_code=400, detail="Driver already ONLINE")

    now = datetime.now(timezone.utc)

    # ✅ MUST: assignment must exist and be valid for current time
    assignment = db.execute(
        select(DriverVehicleAssignment).where(
            and_(
                DriverVehicleAssignment.driver_id == payload.driver_id,
                DriverVehicleAssignment.start_time <= now,
                or_(
                    DriverVehicleAssignment.end_time.is_(None),
                    DriverVehicleAssignment.end_time >= now
                )
            )
        ).order_by(DriverVehicleAssignment.start_time.desc())
    ).scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="No valid vehicle assignment found for current time. You can go ONLINE only during assigned slot."
        )

    # ✅ create shift using assignment details
    shift = DriverShift(
        driver_id=payload.driver_id,
        tenant_id=payload.tenant_id,
        vehicle_id=assignment.vehicle_id,
        status="ONLINE",
        started_at=now,
        ended_at=None,
        expected_end_at=assignment.end_time,
        last_latitude=payload.latitude,
        last_longitude=payload.longitude
    )
    db.add(shift)

    # ✅ update driver_location upsert
    loc = db.execute(
        select(DriverLocation).where(DriverLocation.driver_id == payload.driver_id)
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

    # ✅ location history entry
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
# Rules:
# - Driver must be ONLINE
# - If assignment time ended => auto end shift
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

    # ✅ get active shift
    shift = db.execute(
        select(DriverShift).where(
            and_(
                DriverShift.driver_id == payload.driver_id,
                DriverShift.status == "ONLINE",
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=400, detail="Driver is not ONLINE. Start shift first.")

    # ✅ auto end shift if assignment ended
    if auto_end_shift_if_required(db, shift, now):
        raise HTTPException(
            status_code=400,
            detail="Shift ended automatically because assignment time is completed."
        )

    # ✅ update driver_location (upsert)
    loc = db.execute(
        select(DriverLocation).where(DriverLocation.driver_id == payload.driver_id)
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

    # ✅ location history always
    db.add(DriverLocationHistory(
        driver_id=payload.driver_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        recorded_at=now
    ))

    # ✅ shift last lat lng
    shift.last_latitude = payload.latitude
    shift.last_longitude = payload.longitude

    db.commit()
    db.refresh(loc)
    return loc


# =========================================================
# ✅ 3) End Shift manually (Go OFFLINE)
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
                DriverShift.status == "ONLINE",
                DriverShift.ended_at.is_(None)
            )
        ).order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=404, detail="No active ONLINE shift found")

    shift.status = "OFFLINE"
    shift.ended_at = now

    db.commit()
    return {"message": "Shift ended successfully"}


# =========================================================
# ✅ 4) Get current shift (auto end if expired)
# GET /drivers/{driver_id}/shift/current
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
        raise HTTPException(status_code=404, detail="No active shift found")

    # ✅ auto end shift if expired
    auto_end_shift_if_required(db, shift, now)

    return shift
