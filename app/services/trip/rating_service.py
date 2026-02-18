from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trip.trip_rating import TripRating
from app.models.driver.driver_profile import DriverProfile


def update_driver_avg_rating(db: Session, driver_id: int):
    avg_rating = db.query(func.avg(TripRating.rating)).filter(
        TripRating.ratee_id == driver_id
    ).scalar()

    driver = db.query(DriverProfile).filter(
        DriverProfile.driver_id == driver_id
    ).first()

    if driver:
        driver.rating = round(avg_rating or 5.0, 2)
