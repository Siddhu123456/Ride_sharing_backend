from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time

from app.schemas.enums import (
    TripStatusEnum,
    ApprovalStatusEnum,
    DriverTypeEnum,
    DriverDocumentTypeEnum,
    DriverShiftStatusEnum,
    VehicleCategoryEnum,
)


# Driver profile
class DriverProfileResponse(BaseModel):
    driver_id: int
    full_name: str
    phone: Optional[str]
    driver_type: DriverTypeEnum
    rating: float
    approval_status: ApprovalStatusEnum

    class Config:
        from_attributes = True


# Driver documents
class DriverDocumentUploadRequest(BaseModel):
    document_type: DriverDocumentTypeEnum
    file_url: str
    document_number: Optional[str] = None
    expiry_date: Optional[date] = None


class DriverDocumentResponse(BaseModel):
    document_id: int
    driver_id: int
    document_type: DriverDocumentTypeEnum
    file_url: str
    document_number: Optional[str]
    verification_status: str
    verified_by: Optional[int]
    verified_on: Optional[datetime]
    expiry_date: Optional[date]
    created_on: datetime

    class Config:
        from_attributes = True


class DriverDocumentStatusResponse(BaseModel):
    driver_id: int
    uploaded: List[DriverDocumentResponse]
    missing: List[DriverDocumentTypeEnum]
    all_uploaded: bool
    all_approved: bool
    approved_by_same_admin: bool


# Driver shift
class StartDriverShiftRequest(BaseModel):
    driver_id: int
    tenant_id: int
    latitude: float
    longitude: float


class EndDriverShiftRequest(BaseModel):
    driver_id: int


class DriverShiftResponse(BaseModel):
    shift_id: int
    driver_id: int
    tenant_id: int
    vehicle_id: Optional[int]

    status: DriverShiftStatusEnum   # Current status of the driver shift
    started_at: datetime
    ended_at: Optional[datetime]
    expected_end_at: Optional[datetime]

    last_latitude: Optional[float]
    last_longitude: Optional[float]

    class Config:
        from_attributes = True


# Driver offers
class DriverOfferResponse(BaseModel):
    attempt_id: int
    trip_id: int

    pickup_lat: float
    pickup_lng: float
    pickup_address: str

    drop_lat: float
    drop_lng: float
    drop_address: str

    distance_km: float   # Distance in kilometers (new field)
    fare_amount: float

    sent_at: datetime

    class Config:
        from_attributes = True


class DriverOfferRespondRequest(BaseModel):
    accept: bool


# Driver location
class UpdateDriverLocationRequest(BaseModel):
    driver_id: int
    latitude: float
    longitude: float


class DriverLocationResponse(BaseModel):
    driver_id: int
    latitude: float
    longitude: float
    last_updated: datetime

    class Config:
        from_attributes = True


# Driver vehicle assignments
class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int

    registration_no: str
    category: VehicleCategoryEnum

    make: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None

    start_time: time
    end_time: Optional[time]

    is_active_assignment: bool

    class Config:
        from_attributes = True


class DriverVehicleAssignmentResponse(BaseModel):
    vehicle_id: int
    driver_id: Optional[int]
    driver_name: Optional[str]

    start_time: Optional[time]
    end_time: Optional[time]

    is_active: bool
    created_on: Optional[datetime]

    model_config = {"from_attributes": True}


class ChangeVehicleDriverRequest(BaseModel):
    driver_id: int
    start_time: time
    end_time: time


# Driver dashboard
class DriverDashboardTenant(BaseModel):
    tenant_id: int
    tenant_name: str


class DriverDashboardFleet(BaseModel):
    fleet_id: int
    fleet_name: str


class DriverDashboardTodayStats(BaseModel):
    trip_count: int
    total_earnings: float


class DriverDashboardCurrentShift(BaseModel):
    status: str
    started_at: Optional[datetime] = None


class DriverDashboardSummaryResponse(BaseModel):
    driver_id: int

    tenant: Optional[DriverDashboardTenant] = None
    fleet: Optional[DriverDashboardFleet] = None

    today: DriverDashboardTodayStats
    current_shift: DriverDashboardCurrentShift


# Driver trips
class ActiveTripResponse(BaseModel):
    trip_id: int
    status: TripStatusEnum
    pickup_lat: float
    pickup_lng: float
    pickup_address: Optional[str]
    drop_lat: float
    drop_lng: float
    drop_address: Optional[str]
    fare_amount: float | None

    class Config:
        from_attributes = True


class DriverTripItem(BaseModel):
    trip_id: int
    tenant_name: str
    pickup_address: str
    drop_address: str
    fare_amount: float
    status: TripStatusEnum
    completed_at: Optional[datetime]


class DriverTripListResponse(BaseModel):
    page: int
    limit: int
    total: int
    trips: List[DriverTripItem]


# Driver management / fleet related
class AddDriverToFleetByEmailRequest(BaseModel):
    email: EmailStr
    driver_type: DriverTypeEnum


class FleetDriverResponse(BaseModel):
    id: int
    fleet_id: int
    driver_id: int
    approval_status: str
    start_date: datetime

    class Config:
        from_attributes = True


class PendingDriverResponse(BaseModel):
    driver_id: int
    full_name: str
    approval_status: ApprovalStatusEnum
    driver_type: DriverTypeEnum

    class Config:
        from_attributes = True
