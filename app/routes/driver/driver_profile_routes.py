from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.common.user_session import UserSession
from app.models.common.user import AppUser
from app.models.driver.driver_profile import DriverProfile
from app.schemas.driver_profile import DriverProfileResponse

router = APIRouter(prefix="/driver", tags=["Driver - Profile"])


@router.get("/profile", response_model=DriverProfileResponse)
def get_driver_profile(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    result = db.execute(
        select(AppUser, DriverProfile)
        .join(DriverProfile, DriverProfile.driver_id == AppUser.user_id)
        .where(AppUser.user_id == session.user_id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    user, profile = result

    return {
        "driver_id": user.user_id,
        "full_name": user.full_name,
        "phone": user.phone,
    "driver_type": profile.driver_type,      # Driver type included in response
    "rating": float(profile.rating),          # Rating converted to float
        "approval_status": profile.approval_status
    }

