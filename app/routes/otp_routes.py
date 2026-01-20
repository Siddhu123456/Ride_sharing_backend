from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette import status
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, TripStatusEnum

from app.models.user_session import UserSession
from app.models.trip import Trip

from app.schemas.otp import GenerateOtpResponse, VerifyOtpRequest
from app.services.otp_service import create_trip_otp, verify_trip_otp


router = APIRouter(prefix="/trips", tags=["Trips - OTP"])


# ✅ Driver generates OTP at pickup (only if trip is ASSIGNED to him)
@router.post("/{trip_id}/otp/generate", response_model=GenerateOtpResponse)
def generate_trip_otp(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="OTP can be generated only after ASSIGNED")

    otp = create_trip_otp(db, trip_id, ttl_minutes=5)
    db.commit()

    return GenerateOtpResponse(
        trip_id=trip.trip_id,
        otp_code=otp.otp_code,
        expires_at=otp.expires_at
    )


# ✅ Driver verifies OTP and starts trip => status becomes PICKED_UP
@router.post("/{trip_id}/otp/verify", status_code=status.HTTP_200_OK)
def verify_and_start_trip(
    trip_id: int,
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="OTP verify allowed only when trip is ASSIGNED")

    ok = verify_trip_otp(db, trip_id, payload.otp_code)

    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # ✅ start trip
    trip.status = TripStatusEnum.PICKED_UP
    trip.picked_up_at = datetime.now(timezone.utc)
    trip.updated_by = session.user_id
    trip.updated_on = datetime.now(timezone.utc)

    db.commit()
    return {"message": "OTP verified. Trip started (PICKED_UP)."}
