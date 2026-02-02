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


@router.get("/vehicle/assignment/current", response_model=DriverVehicleAssignmentResponse)
def get_current_vehicle_assignment(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    assignment = db.execute(
        select(DriverVehicleAssignment, Vehicle)
        .join(Vehicle, Vehicle.vehicle_id == DriverVehicleAssignment.vehicle_id)
        .where(DriverVehicleAssignment.driver_id == session.user_id)
        .order_by(DriverVehicleAssignment.start_time.desc())
    ).first()

    if not assignment:
        raise HTTPException(404, "No vehicle assigned")

    a, v = assignment

    return {
        "vehicle_id": v.vehicle_id,
        "category": v.category,
        "start_time": a.start_time,
        "end_time": a.end_time
    }
