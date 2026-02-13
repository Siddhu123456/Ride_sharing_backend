from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel


class FleetAssignDriverToVehicleRequest(BaseModel):
    driver_id: int
    vehicle_id: int
    start_time: time
    end_time: time


class FleetAssignDriverToVehicleResponse(BaseModel):
    assignment_id: int
    fleet_id: int
    driver_id: int
    vehicle_id: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True
