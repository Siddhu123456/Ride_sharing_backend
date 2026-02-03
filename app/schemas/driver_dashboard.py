from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# =====================================================
# Tenant Info
# =====================================================
class DriverDashboardTenant(BaseModel):
    tenant_id: int
    tenant_name: str


# =====================================================
# Fleet Info (Fleet Owner Company)
# =====================================================
class DriverDashboardFleet(BaseModel):
    fleet_id: int
    fleet_name: str


# =====================================================
# Today's Stats
# =====================================================
class DriverDashboardTodayStats(BaseModel):
    trip_count: int
    total_earnings: float


# =====================================================
# Current Shift Info
# =====================================================
class DriverDashboardCurrentShift(BaseModel):
    status: str
    started_at: Optional[datetime] = None


# =====================================================
# Main Dashboard Response
# =====================================================
class DriverDashboardSummaryResponse(BaseModel):
    driver_id: int

    tenant: Optional[DriverDashboardTenant] = None
    fleet: Optional[DriverDashboardFleet] = None

    today: DriverDashboardTodayStats
    current_shift: DriverDashboardCurrentShift
