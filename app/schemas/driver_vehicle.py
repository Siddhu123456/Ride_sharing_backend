from pydantic import BaseModel
from datetime import time
from app.schemas.enums import VehicleCategoryEnum
from typing import Optional


class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int
    category: VehicleCategoryEnum
    start_time: time
    end_time: Optional[time]
