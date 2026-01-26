from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FleetVehicleResponse(BaseModel):
    vehicle_id: int
    category: str
    registration_no: str
    approval_status: str
    status: str

    class Config:
        from_attributes = True


class FleetDriverResponse(BaseModel):
    driver_id: int
    full_name: str
    phone: Optional[str]
    email: Optional[str]
    approval_status: str
    driver_type: str

    class Config:
        from_attributes = True


class VehicleDriverAssignmentResponse(BaseModel):
    assignment_id: int
    driver_id: int
    vehicle_id: int
    start_time: datetime
    end_time: Optional[datetime]

    created_by: Optional[int]

    class Config:
        from_attributes = True
