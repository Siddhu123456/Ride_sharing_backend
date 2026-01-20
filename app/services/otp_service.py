import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.trip_otp import TripOtp


def generate_otp_code() -> str:
    return str(random.randint(1000, 9999))


def create_trip_otp(db: Session, trip_id: int, ttl_minutes: int = 5) -> TripOtp:
    # ✅ if OTP already exists and not expired, reuse (optional)
    existing = db.execute(
        select(TripOtp).where(TripOtp.trip_id == trip_id)
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if existing and existing.expires_at > now and existing.verified is False:
        return existing

    otp = TripOtp(
        trip_id=trip_id,
        otp_code=generate_otp_code(),
        expires_at=now + timedelta(minutes=ttl_minutes),
        verified=False
    )

    db.add(otp)
    db.flush()
    return otp


def verify_trip_otp(db: Session, trip_id: int, otp_code: str) -> bool:
    otp = db.execute(
        select(TripOtp).where(TripOtp.trip_id == trip_id)
    ).scalar_one_or_none()

    if not otp:
        return False

    now = datetime.now(timezone.utc)

    if otp.verified:
        return True

    if otp.expires_at <= now:
        return False

    if otp.otp_code != otp_code:
        return False

    otp.verified = True
    db.flush()
    return True
