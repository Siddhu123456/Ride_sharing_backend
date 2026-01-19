from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.enums import VehicleCategoryEnum

class VehicleCreateRequest(BaseModel):
    category: VehicleCategoryEnum
    registration_no: str
    make: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None

class VehicleResponse(BaseModel):
    vehicle_id: int
    tenant_id: int
    fleet_id: Optional[int]
    category: VehicleCategoryEnum
    registration_no: str
    status: str
    approval_status: str
    created_on: datetime

    class Config:
        from_attributes = True
