from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FleetAssignDriverToVehicleRequest(BaseModel):
    driver_id: int
    vehicle_id: int
    start_time: datetime
    end_time: Optional[datetime] = None  # None = ongoing assignment


class FleetAssignDriverToVehicleResponse(BaseModel):
    assignment_id: int
    fleet_id: int
    driver_id: int
    vehicle_id: int
    start_time: datetime
    end_time: Optional[datetime]

    class Config:
        from_attributes = True
