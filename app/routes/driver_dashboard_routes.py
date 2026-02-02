from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import date

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, TripStatusEnum

from app.models.user_session import UserSession
from app.models.trip import Trip
from app.models.driver_shift import DriverShift
from app.models.tenant import Tenant

from app.schemas.driver_dashboard import DriverDashboardSummaryResponse

router = APIRouter(prefix="/driver/dashboard", tags=["Driver - Dashboard"])


@router.get("/summary", response_model=DriverDashboardSummaryResponse)
def driver_dashboard_summary(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    driver_id = session.user_id
    today = date.today()

    # ---------------------------------------------------
    # 1️⃣ Current shift
    # ---------------------------------------------------
    shift = db.execute(
        select(DriverShift)
        .where(
            DriverShift.driver_id == driver_id,
            DriverShift.ended_at.is_(None)
        )
        .order_by(DriverShift.started_at.desc())
    ).scalar_one_or_none()

    # ---------------------------------------------------
    # 2️⃣ Tenant (from shift or last trip)
    # ---------------------------------------------------
    tenant = None

    if shift:
        tenant = db.execute(
            select(Tenant).where(Tenant.tenant_id == shift.tenant_id)
        ).scalar_one_or_none()
    else:
        tenant = db.execute(
            select(Tenant)
            .join(Trip, Trip.tenant_id == Tenant.tenant_id)
            .where(Trip.driver_id == driver_id)
            .order_by(Trip.created_on.desc())
        ).scalar_one_or_none()

    # ---------------------------------------------------
    # 3️⃣ Today's trip stats
    # ---------------------------------------------------
    stats = db.execute(
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

    trip_count, earnings = stats

    return DriverDashboardSummaryResponse(
        driver_id=driver_id,
        tenant={
            "tenant_id": tenant.tenant_id,
            "tenant_name": tenant.name
        } if tenant else None,
        today={
            "trip_count": trip_count,
            "total_earnings": float(earnings)
        },
        current_shift={
            "status": shift.status if shift else "OFFLINE",
            "started_at": shift.started_at if shift else None
        }
    )
