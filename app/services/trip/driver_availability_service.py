from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy import text


from app.models.core import City
from app.models.driver.driver_shift import DriverShift
from app.models.driver.driver_profile import DriverProfile
from app.models.driver.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.fleet_owner.vehicle import Vehicle

from app.schemas.enums import (
    ApprovalStatusEnum,
    VehicleStatusEnum,
    VehicleCategoryEnum
)


def count_available_drivers_by_vehicle(
    db: Session,
    *,
    city_id: int,
    tenant_id: int,
    pickup_lat: float,
    pickup_lng: float
) -> dict[VehicleCategoryEnum, int]:

    query = text("""
        SELECT
            v.category AS vehicle_category,
            COUNT(DISTINCT ds.driver_id) AS driver_count
        FROM driver_shift ds
        JOIN driver_vehicle_assignment dva
            ON dva.driver_id = ds.driver_id
        JOIN vehicle v
            ON v.vehicle_id = dva.vehicle_id
        JOIN driver_profile dp
            ON dp.driver_id = ds.driver_id
        JOIN city c
            ON c.city_id = :city_id
        WHERE
            ds.tenant_id = :tenant_id
            AND ds.status = 'ONLINE'
            AND ds.ended_at IS NULL
            AND dva.is_active = TRUE
            AND dp.approval_status = 'APPROVED'
            AND v.approval_status = 'APPROVED'
            AND v.status = 'ACTIVE'

            -- Driver inside city boundary
            AND ST_Contains(
                c.boundary,
                ST_SetSRID(
                    ST_Point(ds.last_longitude, ds.last_latitude),
                    4326
                )
            )

            AND ST_DWithin(
                ST_SetSRID(
                    ST_Point(ds.last_longitude, ds.last_latitude),
                    4326
                )::geography,
                ST_SetSRID(
                    ST_Point(:pickup_lng, :pickup_lat),
                    4326
                )::geography,
                10000
            )

        GROUP BY v.category
    """)

    rows = db.execute(
        query,
        {
            "city_id": city_id,
            "tenant_id": tenant_id,
            "pickup_lat": pickup_lat,
            "pickup_lng": pickup_lng
        }
    ).all()

    availability = {row[0]: row[1] for row in rows}

    # Ensure all categories exist
    for category in VehicleCategoryEnum:
        availability.setdefault(category, 0)

    return availability


def get_online_drivers_within_10km(
    db: Session,
    *,
    city_id: int,
    pickup_lat: float,
    pickup_lng: float
):
    query = text("""
        SELECT
            ds.driver_id,
            ds.tenant_id,
            ds.last_latitude,
            ds.last_longitude,
            v.category AS vehicle_category
        FROM driver_shift ds
        JOIN driver_vehicle_assignment dva
            ON dva.driver_id = ds.driver_id
        JOIN vehicle v
            ON v.vehicle_id = dva.vehicle_id
        JOIN driver_profile dp
            ON dp.driver_id = ds.driver_id
        JOIN city c
            ON c.city_id = :city_id
        WHERE
            ds.status = 'ONLINE'
            AND ds.ended_at IS NULL
            AND dva.is_active = TRUE
            AND dp.approval_status = 'APPROVED'
            AND v.approval_status = 'APPROVED'
            AND v.status = 'ACTIVE'

            -- Driver inside city boundary
            AND ST_Contains(
                c.boundary,
                ST_SetSRID(
                    ST_Point(ds.last_longitude, ds.last_latitude),
                    4326
                )
            )

            AND ST_DWithin(
                ST_SetSRID(
                    ST_Point(ds.last_longitude, ds.last_latitude),
                    4326
                )::geography,
                ST_SetSRID(
                    ST_Point(:pickup_lng, :pickup_lat),
                    4326
                )::geography,
                10000
            )
    """)

    return db.execute(
        query,
        {
            "city_id": city_id,
            "pickup_lat": pickup_lat,
            "pickup_lng": pickup_lng
        }
    ).all()