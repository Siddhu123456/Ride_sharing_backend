from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.models.user_session import UserSession
from app.models.trip import Trip
from app.models.tenant import TenantCity  # ✅ ensure correct import path

from app.schemas.trip import TripRequestCreate, TripResponse
from app.services.dispatch_service import create_first_offer

router = APIRouter(prefix="/trips", tags=["Trips - Phase 2"])


@router.post("/request", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def request_trip(
    payload: TripRequestCreate,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    # ✅ tenant must be active in the city
    enabled = db.execute(
        select(TenantCity).where(
            and_(
                TenantCity.tenant_id == payload.tenant_id,
                TenantCity.city_id == payload.city_id,
                TenantCity.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not enabled:
        raise HTTPException(status_code=400, detail="Tenant not active in this city")

    # ✅ create trip
    trip = Trip(
        tenant_id=payload.tenant_id,
        rider_id=session.user_id,
        city_id=payload.city_id,

        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        drop_lat=payload.drop_lat,
        drop_lng=payload.drop_lng,

        vehicle_category=payload.vehicle_category,
        status=TripStatusEnum.REQUESTED,

        created_by=session.user_id
    )

    db.add(trip)
    db.flush()  # ✅ to get trip_id
    print("✅ Trip created with trip_id =", trip.trip_id)
    # ✅ create first offer
    offer = create_first_offer(db, trip, created_by=session.user_id)
    print("✅ create_first_offer returned =", offer)

    db.commit()
    db.refresh(trip)

    # ✅ If no offer -> trip still exists
    return trip
