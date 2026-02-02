from pydantic import BaseModel


class LocationPoint(BaseModel):
    lat: float
    lng: float
    address: str | None


class TripRouteResponse(BaseModel):
    pickup: LocationPoint
    drop: LocationPoint
