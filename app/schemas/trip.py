from pydantic import BaseModel
from app.schemas.enums import (
    VehicleCategoryEnum,
    WalletOwnerEnum,
    WalletTxnReasonEnum,
    WalletTxnDirectionEnum,
)
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# --- Trip creation / responses / fare estimates ---
class TripRequestCreate(BaseModel):
    tenant_id: int
    city_id: int

    pickup_lat: float
    pickup_lng: float
    pickup_address: str

    drop_lat: float
    drop_lng: float
    drop_address: str

    vehicle_category: VehicleCategoryEnum
    fare_amount: float


class TripResponse(BaseModel):
    trip_id: int
    status: str
    fare_amount: float | None

    class Config:
        from_attributes = True


class TripFareEstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    drop_lat: float
    drop_lng: float
    drop_address: str


class TenantFareEstimate(BaseModel):
    tenant_id: int
    tenant_name: str
    vehicle_category: VehicleCategoryEnum
    fare: float
    available_drivers: int
    breakup: dict


class TripFareEstimateResponse(BaseModel):
    city_id: int
    pickup_address: str | None
    drop_address: str | None
    distance_km: float
    estimates: List[TenantFareEstimate]


# --- Trip navigation / routing ---
class LocationPoint(BaseModel):
    lat: float
    lng: float
    address: str | None


class TripRouteResponse(BaseModel):
    pickup: LocationPoint
    drop: LocationPoint


# --- Trip lifecycle ---
class TripCancelRequest(BaseModel):
    reason: Optional[str] = None


class TripCompleteRequest(BaseModel):
    # for now simple completion (later add distance/time from device)
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None


class TripStatusResponse(BaseModel):
    trip_id: int
    status: str
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None

    requested_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


# --- OTP / driver & vehicle snapshots for trips ---
class GenerateOtpResponse(BaseModel):
    trip_id: int
    otp_code: str
    expires_at: datetime


class VerifyOtpRequest(BaseModel):
    otp_code: str


class TripDriverResponse(BaseModel):
    driver_id: int
    name: str
    phone: str


class TripVehicleResponse(BaseModel):
    vehicle_id: Optional[int]
    registration_no: Optional[str]
    model: Optional[str]
    category: Optional[str]


class TripOtpResponse(BaseModel):
    otp: Optional[str]
    driver: Optional[TripDriverResponse]
    vehicle: Optional[TripVehicleResponse]


# --- Fare breakdown ---
class FareBreakdownResponse(BaseModel):
    trip_id: int
    base_fare: float
    distance_fare: float
    time_fare: float
    surge_amount: float
    tax_amount: float
    discount_amount: float
    final_fare: float


# --- Wallet models (included in trip context) ---
class WalletResponse(BaseModel):
    wallet_id: int
    balance: Decimal

    class Config:
        from_attributes = True


class WalletTransactionItem(BaseModel):
    transaction_id: int
    trip_id: Optional[int]

    amount: Decimal
    direction: WalletTxnDirectionEnum
    reason: WalletTxnReasonEnum

    created_on: datetime

    model_config = {
        "from_attributes": True
    }


class WalletTransactionListResponse(BaseModel):
    wallet_id: int
    owner_type: WalletOwnerEnum
    owner_id: int

    balance: Decimal
    transactions: List[WalletTransactionItem]

    page: int
    limit: int
    total: int

    model_config = {
        "from_attributes": True
    }