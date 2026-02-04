from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.core import City
from app.models.driver_shift import DriverShift
from app.models.driver_profile import DriverProfile
from app.models.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.vehicle import Vehicle

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
    """
    Returns:
    {
        VehicleCategoryEnum.AUTO: 12,
        VehicleCategoryEnum.SEDAN: 0,
        VehicleCategoryEnum.SUV: 3
    }
    """

    stmt = (
        select(
            Vehicle.category,
            func.count(func.distinct(DriverShift.driver_id))
        )
        .join(DriverVehicleAssignment,
              DriverVehicleAssignment.vehicle_id == Vehicle.vehicle_id)
        .join(DriverShift,
              DriverShift.driver_id == DriverVehicleAssignment.driver_id)
        .join(DriverProfile,
              DriverProfile.driver_id == DriverShift.driver_id)
        .join(City, City.city_id == city_id)
        .where(
            # Tenant + shift
            DriverShift.tenant_id == tenant_id,
            DriverShift.status == "ONLINE",
            DriverShift.ended_at.is_(None),

            # Active assignment
            DriverVehicleAssignment.is_active.is_(True),

            # Driver approved
            DriverProfile.approval_status == ApprovalStatusEnum.APPROVED,

            # Vehicle valid
            Vehicle.approval_status == ApprovalStatusEnum.APPROVED,
            Vehicle.status == VehicleStatusEnum.ACTIVE,

            # Driver inside city
            func.ST_Contains(
                City.boundary,
                func.ST_SetSRID(
                    func.ST_Point(
                        DriverShift.last_longitude,
                        DriverShift.last_latitude
                    ),
                    4326
                )
            )
        )
        .group_by(Vehicle.category)
    )

    rows = db.execute(stmt).all()

    # Convert to dict
    availability = {row[0]: row[1] for row in rows}

    # Ensure all vehicle categories are present (0 if missing)
    for category in VehicleCategoryEnum:
        availability.setdefault(category, 0)

    return availability
