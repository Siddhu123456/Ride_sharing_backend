from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DriverTenantInfo(BaseModel):
    tenant_id: int
    tenant_name: str


class DriverTodayStats(BaseModel):
    trip_count: int
    total_earnings: float


class DriverCurrentShift(BaseModel):
    status: str
    started_at: Optional[datetime]


class DriverDashboardSummaryResponse(BaseModel):
    driver_id: int
    tenant: Optional[DriverTenantInfo]
    today: DriverTodayStats
    current_shift: DriverCurrentShift
