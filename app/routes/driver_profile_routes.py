from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession
from app.models.user import AppUser
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileResponse

router = APIRouter(prefix="/driver", tags=["Driver - Profile"])


@router.get("/profile", response_model=DriverProfileResponse)
def get_driver_profile(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    driver = db.execute(
        select(AppUser, DriverProfile)
        .join(DriverProfile, DriverProfile.driver_id == AppUser.user_id)
        .where(AppUser.user_id == session.user_id)
    ).first()

    if not driver:
        raise HTTPException(404, "Driver profile not found")

    user, profile = driver

    return {
        "driver_id": user.user_id,
        "full_name": user.full_name,
        "phone": user.phone,
        "rating": profile.rating,
        "approval_status": profile.approval_status
    }
