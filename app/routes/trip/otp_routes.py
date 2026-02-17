from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.role_guard import require_role

from app.schemas.enums import TenantRoleEnum, TripStatusEnum
from app.schemas.otp import GenerateOtpResponse, VerifyOtpRequest

from app.models.trip.trip import Trip
from app.models.trip.trip_otp import TripOtp
from app.models.common.user import AppUser
from app.models.driver.driver_vehicle_assignment import DriverVehicleAssignment
from app.models.fleet_owner.vehicle import Vehicle
from app.models.common.user_session import UserSession

from app.services.trip.otp_service import create_trip_otp, verify_trip_otp

router = APIRouter(prefix="/trips", tags=["Trips"])

# Driver generates OTP at pickup (only if trip is ASSIGNED to him)
@router.post("/{trip_id}/otp/generate", response_model=GenerateOtpResponse)
def generate_trip_otp(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="OTP can be generated only after ASSIGNED")

    otp = create_trip_otp(db, trip_id, ttl_minutes=30)
    db.commit()

    return GenerateOtpResponse(
        trip_id=trip.trip_id,
        otp_code=otp.otp_code,
        expires_at=otp.expires_at
    )


@router.get("/{trip_id}/otp")
def get_trip_otp_with_driver_details(
    trip_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.RIDER))
):
    # Fetch trip
    trip = db.execute(
        select(Trip).where(
            Trip.trip_id == trip_id,
            Trip.rider_id == session.user_id
        )
    ).scalar_one_or_none()

    if not trip:
        raise HTTPException(404, "Trip not found")

    # Driver not assigned yet
    if not trip.driver_id:
        return {
            "otp": None,
            "driver": None,
            "vehicle": None
        }

    # Fetch OTP
    otp = db.execute(
        select(TripOtp).where(TripOtp.trip_id == trip_id)
    ).scalar_one_or_none()

    current_time = datetime.now(timezone.utc)

    otp_code = None
    if otp and otp.expires_at >= current_time:
        otp_code = otp.otp_code

    # Driver details
    driver = db.execute(
        select(AppUser).where(AppUser.user_id == trip.driver_id)
    ).scalar_one()

    # Active vehicle assignment
    assignment = db.execute(
        select(DriverVehicleAssignment)
        .where(
            DriverVehicleAssignment.driver_id == trip.driver_id,
            DriverVehicleAssignment.is_active == True
        )
    ).scalar_one_or_none()

    vehicle = None
    if assignment:
        vehicle = db.execute(
            select(Vehicle)
            .where(Vehicle.vehicle_id == assignment.vehicle_id)
        ).scalar_one_or_none()

    return {
        "otp": otp_code,
        "driver": {
            "driver_id": driver.user_id,
            "name": driver.full_name,
            "phone": driver.phone
        },
        "vehicle": {
            "vehicle_id": vehicle.vehicle_id if vehicle else None,
            "registration_no": vehicle.registration_no if vehicle else None,
            "model": vehicle.model if vehicle else None,
            "category": vehicle.category if vehicle else None
        }
    }




    # Driver verifies OTP and starts trip; status becomes PICKED_UP
@router.post("/{trip_id}/otp/verify", status_code=status.HTTP_200_OK)
def verify_and_start_trip(
    trip_id: int,
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.DRIVER))
):
    trip = db.execute(select(Trip).where(Trip.trip_id == trip_id)).scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="OTP verify allowed only when trip is ASSIGNED")

    ok = verify_trip_otp(db, trip_id, payload.otp_code)

    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Start the trip
    trip.status = TripStatusEnum.PICKED_UP
    trip.picked_up_at = datetime.now(timezone.utc)
    trip.updated_by = session.user_id
    trip.updated_on = datetime.now(timezone.utc)

    db.commit()
    db.refresh(trip)  # Important: refresh trip after commit

    # Match frontend expectation for response
    return {
        "trip_id": trip.trip_id,
        "status": trip.status.value
    }

