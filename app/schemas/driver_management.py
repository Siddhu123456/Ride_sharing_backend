from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.schemas.enums import DriverTypeEnum

class AddDriverToFleetByEmailRequest(BaseModel):
    email: EmailStr
    driver_type: DriverTypeEnum

class FleetDriverResponse(BaseModel):
    id: int
    fleet_id: int
    driver_id: int
    approval_status: str
    start_date: datetime

    class Config:
        from_attributes = True


class PendingDriverResponse(BaseModel):
    driver_id: int
    tenant_id: int
    driver_type: str
    approval_status: str
    created_on: datetime

    class Config:
        from_attributes = True