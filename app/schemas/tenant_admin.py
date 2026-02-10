from datetime import datetime
from typing import List
from pydantic import BaseModel

from app.schemas.enums import ApprovalStatusEnum, DriverTypeEnum


class AssignTenantAdminRequest(BaseModel):
    user_id: int
    is_primary: bool = False


class TenantAdminResponse(BaseModel):
    tenant_admin_id: int
    tenant_id: int
    user_id: int
    is_primary: bool
    is_active: bool
    created_on: datetime

    class Config:
        from_attributes = True


class TenantAdminListResponse(BaseModel):
    tenant_id: int
    admins: List[TenantAdminResponse]


class RemoveTenantAdminResponse(BaseModel):
    message: str

