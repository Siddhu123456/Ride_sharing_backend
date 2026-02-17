from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.trip.trip import Trip
from app.schemas.trip import TripRouteResponse

router = APIRouter(prefix="/trips", tags=["Trips - Navigation"])


@router.get("/{trip_id}/route", response_model=TripRouteResponse)
def get_trip_route(
    trip_id: int,
    db: Session = Depends(get_db)
):
    trip = db.execute(
        select(Trip).where(Trip.trip_id == trip_id)
    ).scalar_one_or_none()

    if not trip:
        raise HTTPException(404, "Trip not found")

    return {
        "pickup": {
            "lat": trip.pickup_lat,
            "lng": trip.pickup_lng,
            "address": trip.pickup_address
        },
        "drop": {
            "lat": trip.drop_lat,
            "lng": trip.drop_lng,
            "address": trip.drop_address
        }
    }
