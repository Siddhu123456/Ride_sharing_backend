from pydantic import BaseModel
from datetime import time
from typing import Optional
from app.schemas.enums import VehicleCategoryEnum


class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int

    registration_no: str
    category: VehicleCategoryEnum

    make: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None

    start_time: time
    end_time: Optional[time]

    is_active_assignment: bool

    class Config:
        from_attributes = True
