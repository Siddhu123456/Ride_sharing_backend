from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, select, text

from app.core.database import get_db
from app.core.role_guard import require_role
from app.models.tenant import Tenant
from app.models.trip import Trip
from app.schemas.enums import TenantRoleEnum

from app.models.user import AppUser
from app.models.user_session import UserSession

from app.schemas.rider import RiderProfileResponse, RiderTripHistoryItem
from app.schemas.rider import RiderCityResponse

router = APIRouter(
    prefix="/rider",
    tags=["Rider - Bootstrap"]
)


@router.get("/profile", response_model=RiderProfileResponse)
def get_rider_profile(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    rider = db.execute(
        select(AppUser).where(AppUser.user_id == session.user_id)
    ).scalar_one_or_none()

    if not rider:
        raise HTTPException(404, "Rider not found")

    return {
        "user_id": rider.user_id,
        "full_name": rider.full_name,
        "phone": rider.phone,
        "email": rider.email,
        "gender": rider.gender,
        "country_code": rider.country_code,
        "status": rider.status,
        "joined_on": rider.created_on
    }


@router.get("/city", response_model=RiderCityResponse)
def detect_rider_city(
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    """
    Detect which city the rider is currently in
    (restricted to rider's country)
    """

    query = text("""
        SELECT c.city_id, c.name, c.country_code
        FROM city c
        JOIN app_user u ON u.country_code = c.country_code
        WHERE u.user_id = :user_id
          AND c.boundary IS NOT NULL
          AND ST_Contains(
              c.boundary,
              ST_SetSRID(ST_Point(:lng, :lat), 4326)
          )
        LIMIT 1
    """)

    city = db.execute(
        query,
        {
            "lat": lat,
            "lng": lng,
            "user_id": session.user_id
        }
    ).mappings().first()

    if not city:
        raise HTTPException(
            status_code=404,
            detail="Service not available in your current location"
        )

    return {
        "city_id": city["city_id"],
        "city_name": city["name"],
        "country_code": city["country_code"]
    }


@router.get("/trips/history", response_model=list[RiderTripHistoryItem])
def get_rider_trip_history(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    """
    Fetch trip history for logged-in rider
    """

    trips = (
        db.query(Trip, Tenant.name.label("tenant_name"))
        .join(Tenant, Tenant.tenant_id == Trip.tenant_id)
        .filter(Trip.rider_id == session.user_id)
        .order_by(desc(Trip.created_at))
        .all()
    )

    history = []

    for trip, tenant_name in trips:
        history.append(
            RiderTripHistoryItem(
                trip_id=trip.trip_id,
                tenant_id=trip.tenant_id,
                tenant_name=tenant_name,

                pickup_address=trip.pickup_address,
                drop_address=trip.drop_address,

                vehicle_category=trip.vehicle_category,
                fare_amount=trip.fare_amount,

                status=trip.status,

                created_at=trip.created_at,
                completed_at=trip.completed_at,
            )
        )

    return history
