from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session

from app.models.user_session import UserSession
from app.models.fleet import Fleet
from app.models.user import AppUser
from app.models.user_role import UserRole
from app.models.driver_profile import DriverProfile
from app.models.fleet_driver import FleetDriver

from app.schemas.enums import TenantRoleEnum
from app.schemas.driver_management import AddDriverToFleetRequest, FleetDriverResponse

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner - Driver Management"])


@router.post("/fleets/{fleet_id}/drivers", response_model=FleetDriverResponse, status_code=status.HTTP_201_CREATED)
def add_driver_to_fleet(
    fleet_id: int,
    payload: AddDriverToFleetRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    # ✅ fleet exists
    fleet = db.execute(
        select(Fleet).where(Fleet.fleet_id == fleet_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    # ✅ only owner can add
    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ driver user exists
    driver_user = db.execute(
        select(AppUser).where(AppUser.user_id == payload.driver_user_id)
    ).scalar_one_or_none()

    if not driver_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ prevent duplicate active mapping
    existing_mapping = db.execute(
        select(FleetDriver).where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.driver_id == payload.driver_user_id,
                FleetDriver.end_date.is_(None)
            )
        )
    ).scalar_one_or_none()

    if existing_mapping:
        raise HTTPException(status_code=400, detail="Driver already added in this fleet")

    # ✅ create fleet_driver mapping
    mapping = FleetDriver(
        fleet_id=fleet_id,
        driver_id=payload.driver_user_id,
        created_by=session.user_id
    )
    db.add(mapping)

    # ✅ assign DRIVER role (if not exists)
    role_exists = db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == payload.driver_user_id,
                UserRole.user_role == TenantRoleEnum.DRIVER,
                UserRole.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not role_exists:
        db.add(UserRole(
            user_id=payload.driver_user_id,
            user_role=TenantRoleEnum.DRIVER,
            is_active=True
        ))

    # ✅ create driver_profile if not exists
    profile = db.execute(
        select(DriverProfile).where(DriverProfile.driver_id == payload.driver_user_id)
    ).scalar_one_or_none()

    if not profile:
        db.add(DriverProfile(
            driver_id=payload.driver_user_id,
            tenant_id=fleet.tenant_id,
            driver_type=payload.driver_type
        ))
    else:
        # ✅ update the driver_type if they are re-added (optional)
        profile.driver_type = payload.driver_type

    db.commit()
    db.refresh(mapping)
    return mapping
