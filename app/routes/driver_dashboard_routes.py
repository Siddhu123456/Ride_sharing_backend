from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import date

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, TripStatusEnum, ApprovalStatusEnum

from app.models.user_session import UserSession
from app.models.trip import Trip
from app.models.driver_shift import DriverShift
from app.models.tenant import Tenant
from app.models.fleet import Fleet
from app.models.fleet_driver import FleetDriver
from app.models.driver_profile import DriverProfile

from app.schemas.driver_dashboard import (
    DriverDashboardSummaryResponse,
    DriverDashboardTenant,
    DriverDashboardFleet,
    DriverDashboardTodayStats,
    DriverDashboardCurrentShift
)

router = APIRouter(prefix="/driver/dashboard", tags=["Driver - Dashboard"])


@router.get("/summary", response_model=DriverDashboardSummaryResponse)
def driver_dashboard_summary(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    driver_id = session.user_id
    today = date.today()

    # =====================================================
    # 1️⃣ Current shift (SAFE)
    # =====================================================
    shift = db.execute(
        select(DriverShift)
        .where(
            DriverShift.driver_id == driver_id,
            DriverShift.ended_at.is_(None)
        )
        .order_by(DriverShift.started_at.desc())
    ).scalars().first()

    # =====================================================
    # 2️⃣ Driver profile → Tenant
    # =====================================================
    driver_profile = db.execute(
        select(DriverProfile)
        .where(DriverProfile.driver_id == driver_id)
    ).scalar_one_or_none()

    tenant = None
    if driver_profile:
        tenant = db.execute(
            select(Tenant)
            .where(Tenant.tenant_id == driver_profile.tenant_id)
        ).scalar_one_or_none()

    # =====================================================
    # 3️⃣ Fleet (current active assignment)
    # =====================================================
    fleet = db.execute(
        select(Fleet)
        .join(FleetDriver, FleetDriver.fleet_id == Fleet.fleet_id)
        .where(
            FleetDriver.driver_id == driver_id,
            FleetDriver.approval_status == ApprovalStatusEnum.APPROVED,
            FleetDriver.end_date.is_(None)
        )
        .order_by(FleetDriver.start_date.desc())
    ).scalars().first()

    # =====================================================
    # 4️⃣ Today's trip stats
    # =====================================================
    trip_count, earnings = db.execute(
        select(
            func.count(Trip.trip_id),
            func.coalesce(func.sum(Trip.fare_amount), 0)
        )
        .where(
            and_(
                Trip.driver_id == driver_id,
                Trip.status == TripStatusEnum.COMPLETED,
                func.date(Trip.completed_at) == today
            )
        )
    ).one()

    # =====================================================
    # 5️⃣ Build typed response (NO dicts)
    # =====================================================
    return DriverDashboardSummaryResponse(
        driver_id=driver_id,

        tenant=DriverDashboardTenant(
            tenant_id=tenant.tenant_id,
            tenant_name=tenant.name
        ) if tenant else None,

        fleet=DriverDashboardFleet(
            fleet_id=fleet.fleet_id,
            fleet_name=fleet.fleet_name
        ) if fleet else None,

        today=DriverDashboardTodayStats(
            trip_count=trip_count,
            total_earnings=float(earnings)
        ),

        current_shift=DriverDashboardCurrentShift(
            status=shift.status if shift else "OFFLINE",
            started_at=shift.started_at if shift else None
        )
    )


