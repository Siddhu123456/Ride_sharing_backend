from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from app.schemas.enums import DriverDocumentTypeEnum

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
