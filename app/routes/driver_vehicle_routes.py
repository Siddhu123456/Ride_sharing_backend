from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user_session

from app.models.user_session import UserSession
from app.models.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.vehicle import Vehicle

from app.schemas.driver_vehicle import DriverVehicleAssignmentResponse

router = APIRouter(prefix="/driver", tags=["Driver - Vehicle"])


@router.get(
    "/vehicle/assignment/current",
    response_model=DriverVehicleAssignmentResponse
)
def get_current_vehicle_assignment(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    """
    Returns the currently assigned vehicle for the driver
    (latest assignment by start_time)
    """

    result = db.execute(
        select(DriverVehicleAssignment, Vehicle)
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .where(DriverVehicleAssignment.driver_id == session.user_id)
        .order_by(DriverVehicleAssignment.start_time.desc())
        .limit(1)
    ).first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No vehicle assigned to driver"
        )

    assignment, vehicle = result

    now_time = datetime.now(timezone.utc).time()

    # Check whether the assignment is currently active
    is_active = (
        assignment.start_time <= now_time and
        (assignment.end_time is None or now_time <= assignment.end_time)
    )

    return DriverVehicleAssignmentResponse(
        vehicle_id=vehicle.vehicle_id,
        registration_no=vehicle.registration_no,
        category=vehicle.category,

        make=vehicle.make,
        model=vehicle.model,
        year_of_manufacture=vehicle.year_of_manufacture,

        start_time=assignment.start_time,
        end_time=assignment.end_time,

        is_active_assignment=is_active
    )
