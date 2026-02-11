from pydantic import BaseModel
from typing import List
from datetime import datetime


class TenantAdminProfileResponse(BaseModel):
    user_id: int
    full_name: str
    phone: str
    email: str | None
    gender: str | None

    tenant_id: int
    tenant_name: str

    countries: List[str]

    created_on: datetime

    model_config = {
        "from_attributes": True
    }
