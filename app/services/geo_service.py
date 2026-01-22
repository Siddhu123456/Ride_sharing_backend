from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_Contains, ST_SetSRID, ST_Point

from app.models.core import City, Zone


def find_city_by_gps(db: Session, lat: float, lng: float) -> Optional[City]:
    """
    Returns city where the point lies inside boundary polygon.
    """
    point = ST_SetSRID(ST_Point(lng, lat), 4326)

    city = db.execute(
        select(City).where(
            City.boundary.isnot(None),
            ST_Contains(City.boundary, point)
        )
    ).scalar_one_or_none()

    return city


def find_zone_by_gps(db: Session, city_id: int, lat: float, lng: float) -> Optional[Zone]:
    """
    Returns zone where the point lies inside zone boundary polygon.
    """
    point = ST_SetSRID(ST_Point(lng, lat), 4326)

    zone = db.execute(
        select(Zone).where(
            Zone.city_id == city_id,
            Zone.boundary.isnot(None),
            ST_Contains(Zone.boundary, point)
        )
    ).scalar_one_or_none()

    return zone


def detect_city_and_zone(
    db: Session,
    lat: float,
    lng: float
) -> Tuple[Optional[int], Optional[int]]:
    """
    Returns (city_id, zone_id) or (None, None)
    """
    city = find_city_by_gps(db, lat, lng)
    if not city:
        return None, None

    zone = find_zone_by_gps(db, city.city_id, lat, lng)
    return city.city_id, zone.zone_id if zone else None
