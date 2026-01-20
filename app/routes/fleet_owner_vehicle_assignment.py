from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role
from app.models.fleet import Fleet
from app.models.fleet_driver import FleetDriver
from app.models.user_session import UserSession
from app.models.vehicle import Vehicle
from app.models.driver_vehicle_assignment import DriverVehicleAssignment
from app.schemas.enums import TenantRoleEnum

from app.schemas.fleet_vehicle_assignment import (
    FleetAssignDriverToVehicleRequest,
    FleetAssignDriverToVehicleResponse
)

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner Vehicle Assignment"])


@router.get("/fleets/{fleet_id}/vehicles")
def list_fleet_vehicles(
        fleet_id: int,
        db: Session = Depends(get_db),
        session: UserSession = Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    vehicles = db.execute(
        select(Vehicle).where(
            and_(
                Vehicle.fleet_id == fleet_id,
                Vehicle.approval_status == "APPROVED",
                Vehicle.status == "ACTIVE"
            )
        )
    ).scalars().all()

    return {"vehicles": vehicles}


@router.get("/fleets/{fleet_id}/drivers/available")
def list_available_drivers_for_vehicle(
    fleet_id: int,
    vehicle_id: int,  # ✅ from query param ?vehicle_id=1
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.FLEET_OWNER))
):
    """
    ✅ Returns drivers who:
    - belong to fleet
    - approved in fleet_driver
    - not currently assigned to any vehicle
    - driver_profile.driver_type matches vehicle.category
    """

    # ✅ 1) Get vehicle and its category
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

    vehicle_category = vehicle.category  # BIKE / AUTO / CAB / AC-CAB

    # ✅ 2) DriverProfile.driver_type should match Vehicle.category
    # mapping example:
    # vehicle.category = "BIKE" => driver_type = "BIKE"
    # vehicle.category = "AUTO" => driver_type = "AUTO"
    # vehicle.category = "CAB" or "AC-CAB" => driver_type = "CAB"

    if vehicle_category == "AC-CAB":
        required_driver_type = "CAB"
    else:
        required_driver_type = vehicle_category

    # ✅ 3) Fetch only available drivers
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

                # ✅ exclude drivers who already have active assignment
                ~FleetDriver.driver_id.in_(
                    select(DriverVehicleAssignment.driver_id).where(
                        DriverVehicleAssignment.end_time.is_(None)
                    )
                )
            )
        )
    ).all()

    drivers = [
        {
            "driver_id": row.driver_id,
            "full_name": row.full_name,
            "phone": row.phone,
            "email": row.email,
            "driver_type": row.driver_type
        }
        for row in result
    ]

    return {
        "fleet_id": fleet_id,
        "vehicle_id": vehicle_id,
        "vehicle_category": vehicle_category,
        "required_driver_type": required_driver_type,
        "drivers": drivers
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
    # ✅ 1) fleet must exist
    fleet = db.execute(
        select(Fleet).where(Fleet.fleet_id == fleet_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    # ✅ 2) driver must belong to that fleet
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
        raise HTTPException(
            status_code=400,
            detail="Driver is not linked to this fleet"
        )

    # ✅ 3) vehicle must belong to the same fleet
    vehicle = db.execute(
        select(Vehicle).where(
            and_(
                Vehicle.vehicle_id == payload.vehicle_id,
                Vehicle.fleet_id == fleet_id
            )
        )
    ).scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=400,
            detail="Vehicle does not belong to this fleet"
        )

    # ✅ 4) Validate end_time > start_time
    if payload.end_time is not None and payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    # ✅ 5) prevent driver assigned to another vehicle currently
    # only check if this assignment is CURRENT (end_time = null)
    if payload.end_time is None:
        active_driver_assignment = db.execute(
            select(DriverVehicleAssignment).where(
                and_(
                    DriverVehicleAssignment.driver_id == payload.driver_id,
                    DriverVehicleAssignment.end_time.is_(None)
                )
            )
        ).scalar_one_or_none()

        if active_driver_assignment:
            raise HTTPException(
                status_code=409,
                detail="Driver already assigned to another vehicle currently"
            )

    # ✅ 6) Prevent overlapping assignments for this vehicle
    # overlap logic supports both bounded and ongoing assignments
    if payload.end_time is None:
        # new assignment ongoing => overlap if any assignment is active after start_time
        overlap = db.execute(
            select(DriverVehicleAssignment).where(
                and_(
                    DriverVehicleAssignment.vehicle_id == payload.vehicle_id,
                    or_(
                        DriverVehicleAssignment.end_time.is_(None),
                        DriverVehicleAssignment.end_time > payload.start_time
                    )
                )
            )
        ).scalar_one_or_none()
    else:
        # bounded assignment overlap check
        overlap = db.execute(
            select(DriverVehicleAssignment).where(
                and_(
                    DriverVehicleAssignment.vehicle_id == payload.vehicle_id,
                    DriverVehicleAssignment.start_time < payload.end_time,
                    or_(
                        DriverVehicleAssignment.end_time.is_(None),
                        DriverVehicleAssignment.end_time > payload.start_time
                    )
                )
            )
        ).scalar_one_or_none()

    if overlap:
        raise HTTPException(
            status_code=409,
            detail="Vehicle already assigned to another driver in that time slot"
        )

    # ✅ 7) create assignment
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
