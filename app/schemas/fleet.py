from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time, date
from decimal import Decimal

from app.schemas.enums import (
    FleetDocumentTypeEnum,
    ApprovalStatusEnum,
    SettlementStatusEnum,
    VehicleDocumentTypeEnum,
    VehicleCategoryEnum,
)


# Fleet overview responses
class FleetVehicleResponse(BaseModel):
    vehicle_id: int
    category: str
    registration_no: str
    approval_status: str
    status: str

    class Config:
        from_attributes = True


class FleetDriverResponse(BaseModel):
    driver_id: int
    full_name: str
    phone: Optional[str]
    email: Optional[str]
    approval_status: str
    driver_type: str

    class Config:
        from_attributes = True


class VehicleDriverAssignmentResponse(BaseModel):
    assignment_id: int
    driver_id: int
    vehicle_id: int
    start_time: time
    end_time: time

    created_by: Optional[int]

    class Config:
        from_attributes = True


# Fleet documents
class FleetDocumentUploadRequest(BaseModel):
    document_type: FleetDocumentTypeEnum
    file_url: str
    document_number: Optional[str] = None


class FleetDocumentResponse(BaseModel):
    document_id: int
    fleet_id: int
    document_type: FleetDocumentTypeEnum
    file_url: str
    document_number: Optional[str]
    verification_status: ApprovalStatusEnum
    verified_by: Optional[int]
    verified_on: Optional[datetime]
    created_on: datetime

    class Config:
        from_attributes = True


class FleetDocumentStatusResponse(BaseModel):
    fleet_id: int
    uploaded: List[FleetDocumentResponse]
    missing: List[FleetDocumentTypeEnum]
    all_uploaded: bool
    all_approved: bool
    approved_by_same_admin: bool


# Fleet vehicle assignment
class FleetAssignDriverToVehicleRequest(BaseModel):
    driver_id: int
    vehicle_id: int
    start_time: time
    end_time: time


class FleetAssignDriverToVehicleResponse(BaseModel):
    assignment_id: int
    fleet_id: int
    driver_id: int
    vehicle_id: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True


# Fleet admin
class FleetPendingResponse(BaseModel):
    fleet_id: int
    tenant_id: int
    owner_user_id: int
    fleet_name: str
    approval_status: str
    status: str
    created_on: datetime

    class Config:
        from_attributes = True


class FleetApprovalRequest(BaseModel):
    approve: bool
    note: Optional[str] = None


# Fleet verification
class VerifyFleetDocumentRequest(BaseModel):
    approve: bool


# Fleet owner apply
class FleetApplyRequest(BaseModel):
    tenant_id: int
    fleet_name: str


class FleetApplyResponse(BaseModel):
    fleet_id: int
    tenant_id: int
    owner_user_id: int
    fleet_name: str
    approval_status: str
    status: str
    created_on: datetime

    class Config:
        from_attributes = True


# Fleet settlements
class FleetSettlementTripItem(BaseModel):
    trip_id: int
    commission_amount: Decimal


class FleetSettlementResponse(BaseModel):
    settlement_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime
    paid_on: datetime | None
    trips: List[FleetSettlementTripItem]


class FleetSettlementPayResponse(BaseModel):
    settlement_id: int
    status: SettlementStatusEnum
    paid_on: datetime


class SettlementTripItem(BaseModel):
    trip_id: int
    commission_amount: Decimal

    model_config = {
        "from_attributes": True
    }


class SettlementTransactionItem(BaseModel):
    transaction_id: int
    wallet_id: int
    amount: Decimal
    direction: str
    reason: str
    created_on: datetime

    model_config = {
        "from_attributes": True
    }


class FleetSettlementHistoryItem(BaseModel):
    settlement_id: int
    total_commission: Decimal
    status: SettlementStatusEnum
    created_on: datetime
    paid_on: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


# --- Vehicle (owner) models ---
class VehicleCreateRequest(BaseModel):
    category: VehicleCategoryEnum
    registration_no: str
    make: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None


class VehicleResponse(BaseModel):
    vehicle_id: int
    tenant_id: int
    fleet_id: Optional[int]
    category: VehicleCategoryEnum
    registration_no: str
    status: str
    approval_status: str
    created_on: datetime

    class Config:
        from_attributes = True


# --- Vehicle documents ---
class VehicleDocumentUploadRequest(BaseModel):
    document_type: VehicleDocumentTypeEnum
    file_url: str


class VehicleDocumentResponse(BaseModel):
    document_id: int
    vehicle_id: int
    document_type: VehicleDocumentTypeEnum
    file_url: str
    verification_status: str
    verified_by: int | None
    verified_on: datetime | None
    created_on: datetime

    class Config:
        from_attributes = True


class VehicleDocStatusResponse(BaseModel):
    vehicle_id: int
    uploaded: List[VehicleDocumentResponse]
    missing: List[VehicleDocumentTypeEnum]
    all_uploaded: bool
    all_approved: bool
    approved_by_same_admin: bool


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
    
    
class PendingVehicleResponse(BaseModel):
    vehicle_id: int
    vehicle_model: Optional[str]

    class Config:
        from_attributes = True
