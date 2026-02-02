from pydantic import BaseModel
from app.schemas.enums import ApprovalStatusEnum
from typing import Optional


class DriverProfileResponse(BaseModel):
    driver_id: int
    full_name: str
    phone: Optional[str]
    rating: float
    approval_status: ApprovalStatusEnum
