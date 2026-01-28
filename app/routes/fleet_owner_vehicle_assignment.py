from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role
from app.models.driver_profile import DriverProfile
from app.models.fleet import Fleet
from app.models.fleet_driver import FleetDriver
from app.models.user import AppUser
from app.models.user_session import UserSession
from app.models.vehicle import Vehicle
from app.models.driver_vehicle_assignment import DriverVehicleAssignment
from app.schemas.enums import TenantRoleEnum

from app.schemas.fleet_vehicle_assignment import (
    FleetAssignDriverToVehicleRequest,
    FleetAssignDriverToVehicleResponse
)

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner Vehicle Assignment"])

# @router.get("/fleets/{fleet_id}/vehicles")
# def list_fleet_vehicles(
#         fleet_id: int,
#         db: Session = Depends(get_db),
#         session: UserSession = Depends(require_role(TenantRoleEnum.FLEET_OWNER))
# ):
#     vehicles = db.execute(
#         select(Vehicle).where(
#             and_(
#                 Vehicle.fleet_id == fleet_id,
#                 Vehicle.approval_status == "APPROVED",
#                 Vehicle.status == "ACTIVE"
#             )
#         )
#     ).scalars().all()

#     return {"vehicles": vehicles}

@router.get("/fleets/{fleet_id}/drivers/available")
def list_available_drivers_for_vehicle(
    fleet_id: int,
    vehicle_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    vehicle = db.execute(
        select(Vehicle).where(
            and_(
                Vehicle.vehicle_id == vehicle_id,
                Vehicle.fleet_id == fleet_id
            )
        )
    ).scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found in this fleet")

    vehicle_category = vehicle.category
    required_driver_type = "CAB" if vehicle_category == "AC-CAB" else vehicle_category

    result = db.execute(
        select(
            FleetDriver.driver_id,
            AppUser.full_name,
            AppUser.phone,
            AppUser.email,
            DriverProfile.driver_type
        )
        .join(AppUser, AppUser.user_id == FleetDriver.driver_id)
        .join(DriverProfile, DriverProfile.driver_id == FleetDriver.driver_id)
        .where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.end_date.is_(None),
                FleetDriver.approval_status == "APPROVED",
                DriverProfile.driver_type == required_driver_type,
                ~FleetDriver.driver_id.in_(
                    select(DriverVehicleAssignment.driver_id)
                )
            )
        )
    ).all()

    return {
        "fleet_id": fleet_id,
        "vehicle_id": vehicle_id,
        "vehicle_category": vehicle_category,
        "required_driver_type": required_driver_type,
        "drivers": [
            {
                "driver_id": r.driver_id,
                "full_name": r.full_name,
                "phone": r.phone,
                "email": r.email,
                "driver_type": r.driver_type
            }
            for r in result
        ]
    }


@router.post(
    "/fleets/{fleet_id}/assign-driver",
    response_model=FleetAssignDriverToVehicleResponse,
    status_code=status.HTTP_201_CREATED
)
def assign_fleet_driver_to_vehicle(
    fleet_id: int,
    payload: FleetAssignDriverToVehicleRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    fleet = db.execute(
        select(Fleet).where(Fleet.fleet_id == fleet_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    fleet_driver = db.execute(
        select(FleetDriver).where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.driver_id == payload.driver_id,
                FleetDriver.end_date.is_(None)
            )
        )
    ).scalar_one_or_none()

    if not fleet_driver:
        raise HTTPException(status_code=400, detail="Driver is not linked to this fleet")

    vehicle = db.execute(
        select(Vehicle).where(
            and_(
                Vehicle.vehicle_id == payload.vehicle_id,
                Vehicle.fleet_id == fleet_id
            )
        )
    ).scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=400, detail="Vehicle does not belong to this fleet")

    # ✅ TIME vs TIME validation
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    # ✅ prevent driver being active elsewhere
    active_driver_assignment = db.execute(
        select(DriverVehicleAssignment).where(
            DriverVehicleAssignment.driver_id == payload.driver_id
        )
    ).scalar_one_or_none()

    if active_driver_assignment:
        raise HTTPException(
            status_code=409,
            detail="Driver already assigned to another vehicle"
        )

    # ✅ OVERLAP CHECK (TIME vs TIME ONLY)
    overlap = db.execute(
        select(DriverVehicleAssignment).where(
            and_(
                DriverVehicleAssignment.vehicle_id == payload.vehicle_id,
                DriverVehicleAssignment.start_time < payload.end_time,
                DriverVehicleAssignment.end_time > payload.start_time
            )
        )
    ).scalar_one_or_none()

    if overlap:
        raise HTTPException(
            status_code=409,
            detail="Vehicle already assigned to another driver in that time slot"
        )

    assignment = DriverVehicleAssignment(
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        created_by=fleet.owner_user_id
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return FleetAssignDriverToVehicleResponse(
        assignment_id=assignment.assignment_id,
        fleet_id=fleet_id,
        driver_id=assignment.driver_id,
        vehicle_id=assignment.vehicle_id,
        start_time=assignment.start_time,
        end_time=assignment.end_time
    )
