from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FleetPendingResponse(BaseModel):
    fleet_id: int
    tenant_id: int
    owner_user_id: int
    fleet_name: str
    approval_status: str
    status: str
    created_on: datetime

    class Config:
        from_attributes = True


class FleetApprovalRequest(BaseModel):
    approve: bool
    note: Optional[str] = None  # future use
