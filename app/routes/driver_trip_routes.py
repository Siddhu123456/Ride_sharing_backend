from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.core.role_guard import require_role
from app.models.tenant import Tenant
from app.models.user_session import UserSession
from app.models.trip import Trip
from app.schemas.driver_trip import ActiveTripResponse, DriverTripItem, DriverTripListResponse
from app.schemas.enums import TenantRoleEnum, TripStatusEnum

router = APIRouter(prefix="/driver/trips", tags=["Driver - Trips"])


@router.get("/active", response_model=ActiveTripResponse | None)
def get_active_trip(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    trip = db.execute(
        select(Trip).where(
            Trip.driver_id == session.user_id,
            Trip.status.in_([
                TripStatusEnum.ASSIGNED,
                TripStatusEnum.PICKED_UP
            ])
        )
    ).scalar_one_or_none()

    return trip


@router.get("/trips", response_model=DriverTripListResponse)
def list_driver_trips(
    status: TripStatusEnum | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),

    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    driver_id = session.user_id
    offset = (page - 1) * limit

    filters = [Trip.driver_id == driver_id]

    if status:
        filters.append(Trip.status == status)

    if from_date:
        filters.append(func.date(Trip.created_on) >= from_date)

    if to_date:
        filters.append(func.date(Trip.created_on) <= to_date)

    # ---------------------------------------------------
    # Total count
    # ---------------------------------------------------
    total = db.execute(
        select(func.count(Trip.trip_id)).where(and_(*filters))
    ).scalar()

    # ---------------------------------------------------
    # Fetch trips
    # ---------------------------------------------------
    rows = db.execute(
        select(Trip, Tenant.name)
        .join(Tenant, Tenant.tenant_id == Trip.tenant_id)
        .where(and_(*filters))
        .order_by(Trip.created_on.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    trips = [
        DriverTripItem(
            trip_id=trip.trip_id,
            tenant_name=tenant_name,
            pickup_address=trip.pickup_address,
            drop_address=trip.drop_address,
            fare_amount=trip.fare_amount,
            status=trip.status,
            completed_at=trip.completed_at
        )
        for trip, tenant_name in rows
    ]

    return DriverTripListResponse(
        page=page,
        limit=limit,
        total=total,
        trips=trips
    )
