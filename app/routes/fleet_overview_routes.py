from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum

from app.models.fleet import Fleet
from app.models.vehicle import Vehicle
from app.models.fleet_driver import FleetDriver
from app.models.driver_profile import DriverProfile
from app.models.user import AppUser
from app.models.driver_vehicle_assignment import DriverVehicleAssignment

from app.schemas.fleet_overview import (
    FleetVehicleResponse,
    FleetDriverResponse,
    VehicleDriverAssignmentResponse
)

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner - Overview"])


# ✅ Get all vehicles in fleet
@router.get("/fleets/{fleet_id}/vehicles", response_model=list[FleetVehicleResponse])
def get_fleet_vehicles(
    fleet_id: int,
    db: Session = Depends(get_db),
    session=Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    vehicles = db.execute(
        select(Vehicle).where(Vehicle.fleet_id == fleet_id)
    ).scalars().all()
    print('return vehicles')
    return vehicles


# ✅ Get all drivers in fleet
@router.get("/fleets/{fleet_id}/drivers", response_model=list[FleetDriverResponse])
def get_fleet_drivers(
    fleet_id: int,
    db: Session = Depends(get_db),
    session=Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    result = db.execute(
        select(
            FleetDriver.driver_id,
            AppUser.full_name,
            AppUser.phone,
            AppUser.email,
            FleetDriver.approval_status,
            DriverProfile.driver_type
        )
        .join(AppUser, AppUser.user_id == FleetDriver.driver_id)
        .join(DriverProfile, DriverProfile.driver_id == FleetDriver.driver_id)
        .where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.end_date.is_(None)  # ✅ current active drivers only
            )
        )
    ).all()

    drivers = [
        FleetDriverResponse(
            driver_id=row.driver_id,
            full_name=row.full_name,
            phone=row.phone,
            email=row.email,
            approval_status=row.approval_status,
            driver_type=row.driver_type
        )
        for row in result
    ]

    return drivers


# ✅ Get vehicle-driver assignments (history + current)
@router.get(
    "/fleets/{fleet_id}/assignments",
    response_model=list[VehicleDriverAssignmentResponse]
)
def get_fleet_vehicle_driver_assignments(
    fleet_id: int,
    db: Session = Depends(get_db),
    session=Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    assignments = db.execute(
        select(DriverVehicleAssignment)
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .where(Vehicle.fleet_id == fleet_id)
        .order_by(DriverVehicleAssignment.start_time.desc())
    ).scalars().all()

    return assignments


# ✅ Get current assignment of a vehicle (if any)
@router.get(
    "/vehicles/{vehicle_id}/current-assignment",
    response_model=VehicleDriverAssignmentResponse | None
)
def get_vehicle_current_assignment(
    vehicle_id: int,
    db: Session = Depends(get_db),
    session=Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    vehicle = db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == vehicle.fleet_id)).scalar_one_or_none()
    if not fleet or fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    assignment = db.execute(
        select(DriverVehicleAssignment).where(
            and_(
                DriverVehicleAssignment.vehicle_id == vehicle_id,
                DriverVehicleAssignment.end_time.is_(None)
            )
        )
    ).scalar_one_or_none()

    return assignment
