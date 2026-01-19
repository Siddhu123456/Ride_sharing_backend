from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.schemas.enums import VehicleDocumentTypeEnum

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
