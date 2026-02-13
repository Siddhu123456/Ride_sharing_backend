from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.enums import FleetDocumentTypeEnum


class FleetApplyRequest(BaseModel):
    tenant_id: int
    fleet_name: str


class FleetApplyResponse(BaseModel):
    fleet_id: int
    tenant_id: int
    owner_user_id: int
    fleet_name: str
    approval_status: str
    status: str
    created_on: datetime

    class Config:
        from_attributes = True

