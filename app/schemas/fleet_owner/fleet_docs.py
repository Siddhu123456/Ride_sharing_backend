from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.enums import FleetDocumentTypeEnum, ApprovalStatusEnum


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
    uploaded: List[FleetDocumentResponse]              # actual documents present
    missing: List[FleetDocumentTypeEnum]               # missing doc types
    all_uploaded: bool
    all_approved: bool
    approved_by_same_admin: bool
