from pydantic import BaseModel
from typing import Optional
from app.schemas.enums import ApprovalStatusEnum, DriverTypeEnum


class DriverProfileResponse(BaseModel):
    driver_id: int
    full_name: str
    phone: Optional[str]
    driver_type: DriverTypeEnum
    rating: float
    approval_status: ApprovalStatusEnum

    class Config:
        from_attributes = True
