from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.driver_docs import DriverDocumentResponse
from app.schemas.driver_management import PendingDriverResponse
from app.schemas.enums import TenantRoleEnum, ApprovalStatusEnum

from app.models.user_session import UserSession
from app.models.tenant_admin import TenantAdmin
from app.models.driver_document import DriverDocument
from app.models.driver_profile import DriverProfile

from app.schemas.fleet_verify import VerifyFleetDocumentRequest  # reuse {approve: bool}

from app.services.driver_workflow import (
    get_uploaded_driver_docs,
    compute_driver_doc_status,
    auto_approve_driver_if_ready
)

router = APIRouter(prefix="/tenant-admin/drivers", tags=["Tenant Admin - Driver Verification"])

# ✅ 1) LIST PENDING DRIVERS (like fleets pending)
@router.get("/pending", response_model=List[PendingDriverResponse])
def list_pending_drivers(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    drivers = db.execute(
        select(DriverProfile)
        .join(DriverDocument, DriverDocument.driver_id == DriverProfile.driver_id)
        .where(
            DriverProfile.tenant_id == tenant_admin.tenant_id,
            DriverProfile.approval_status == ApprovalStatusEnum.PENDING
        )
        .distinct()
    ).scalars().all()

    return drivers


# ✅ 2) GET DRIVER DOCUMENTS (like fleet documents)
@router.get("/{driver_id}/documents", response_model=List[DriverDocumentResponse])
def get_driver_documents(
    driver_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    # ✅ ensure driver belongs to same tenant
    driver_profile = db.execute(
        select(DriverProfile).where(DriverProfile.driver_id == driver_id)
    ).scalar_one_or_none()

    if not driver_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    if driver_profile.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    docs = db.execute(
        select(DriverDocument).where(DriverDocument.driver_id == driver_id)
    ).scalars().all()

    return docs

@router.post("/documents/{document_id}/verify", status_code=200)
def verify_driver_document(
    document_id: int,
    payload: VerifyFleetDocumentRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    doc = db.execute(
        select(DriverDocument).where(DriverDocument.document_id == document_id)
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Driver document not found")

    profile = db.execute(
        select(DriverProfile).where(DriverProfile.driver_id == doc.driver_id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=400, detail="Driver profile not created")

    # ✅ tenant restriction
    if profile.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    # ✅ must upload all docs before verification
    uploaded_docs = get_uploaded_driver_docs(db, doc.driver_id)
    missing, all_uploaded, _, _ = compute_driver_doc_status(uploaded_docs)

    if not all_uploaded:
        raise HTTPException(
            status_code=400,
            detail=f"All required docs must be uploaded before verification. Missing: {missing}"
        )

    # ✅ same tenant admin rule
    already_started_by_other_admin = any(
        d.verified_by is not None and d.verified_by != session.user_id
        for d in uploaded_docs
    )
    if already_started_by_other_admin:
        raise HTTPException(
            status_code=409,
            detail="Another tenant admin started verification. Same admin must approve all docs."
        )

    doc.verification_status = ApprovalStatusEnum.APPROVED if payload.approve else ApprovalStatusEnum.REJECTED
    doc.verified_by = session.user_id
    doc.verified_on = datetime.now(timezone.utc)

    driver_auto_approved = False
    if payload.approve:
        driver_auto_approved = auto_approve_driver_if_ready(db, doc.driver_id)

    db.commit()

    return {
        "message": "Driver document verified successfully",
        "driver_auto_approved": driver_auto_approved
    }
