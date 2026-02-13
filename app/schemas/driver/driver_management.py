from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.schemas.enums import ApprovalStatusEnum, DriverTypeEnum

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
    full_name: str
    approval_status: ApprovalStatusEnum
    driver_type: DriverTypeEnum

    class Config:
        from_attributes = True
