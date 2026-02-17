from sqlalchemy.orm import Session
from sqlalchemy import text


def detect_city_by_location(db: Session, lat: float, lng: float) -> int | None:
    """
    Detect city using PostGIS boundary polygon
    """
    query = text("""
        SELECT city_id
        FROM city
        WHERE boundary IS NOT NULL
        AND ST_Contains(
            boundary,
            ST_SetSRID(ST_Point(:lng, :lat), 4326)
        )
        LIMIT 1
    """)

    return db.execute(query, {"lat": lat, "lng": lng}).scalar_one_or_none()
