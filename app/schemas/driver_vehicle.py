from pydantic import BaseModel
from datetime import time, datetime
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


class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int
    driver_id: Optional[int]
    driver_name: Optional[str]

    start_time: Optional[time]
    end_time: Optional[time]

    is_active: bool
    created_on: Optional[datetime]

    model_config = {"from_attributes": True}


class ChangeVehicleDriverRequest(BaseModel):
    driver_id: int
    start_time: time
    end_time: time
