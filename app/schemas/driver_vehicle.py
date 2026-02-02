from pydantic import BaseModel
from datetime import time
from app.schemas.enums import VehicleCategoryEnum
from typing import Optional


class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int
    vehicle_number: str
    category: str

    brand: Optional[str]
    model: Optional[str]
    color: Optional[str]

    start_time: time
    end_time: Optional[time]

    is_active_assignment: bool

    class Config:
        from_attributes = True
