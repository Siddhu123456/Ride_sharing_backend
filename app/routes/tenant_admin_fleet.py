from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, ApprovalStatusEnum

from app.models.user_session import UserSession
from app.models.tenant_admin import TenantAdmin
from app.models.fleet import Fleet
from app.models.fleet_document import FleetDocument

from app.schemas.fleet_admin import FleetPendingResponse
from app.schemas.fleet_verify import VerifyFleetDocumentRequest
from app.schemas.fleet_docs import FleetDocumentResponse

from app.services.fleet_workflow import (
    get_fleet_uploaded_docs,
    compute_doc_status,
    auto_approve_fleet_if_ready
)

router = APIRouter(prefix="/tenant-admin/fleets", tags=["Tenant Admin - Fleet Verification"])


# ✅ List pending fleet applications in this tenant
@router.get("/pending", response_model=list[FleetPendingResponse])
def list_pending_fleets(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN))
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    fleets = db.execute(
        select(Fleet).where(
            and_(
                Fleet.tenant_id == tenant_admin.tenant_id,
                Fleet.approval_status == ApprovalStatusEnum.PENDING
            )
        )
    ).scalars().all()

    return fleets


# ✅ Tenant admin views fleet documents
@router.get("/{fleet_id}/documents", response_model=list[FleetDocumentResponse])
def get_fleet_documents(
    fleet_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN))
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    docs = db.execute(
        select(FleetDocument).where(FleetDocument.fleet_id == fleet_id)
    ).scalars().all()

    return docs


# ✅ Verify single document (auto approves fleet if last doc approved)
@router.post("/documents/{document_id}/verify", status_code=200)
def verify_fleet_document(
    document_id: int,
    payload: VerifyFleetDocumentRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN))
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    doc = db.execute(
        select(FleetDocument).where(FleetDocument.document_id == document_id)
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == doc.fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    # ✅ Tenant restriction
    if fleet.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    # ✅ all docs must be uploaded before verification
    uploaded_docs = get_fleet_uploaded_docs(db, fleet.fleet_id)
    missing, all_uploaded, _, _ = compute_doc_status(uploaded_docs)

    if not all_uploaded:
        raise HTTPException(
            status_code=400,
            detail=f"All 4 documents must be uploaded before verification. Missing: {missing}"
        )

    # ✅ same admin must approve ALL docs
    already_started_by_other_admin = any(
        d.verified_by is not None and d.verified_by != session.user_id
        for d in uploaded_docs
    )

    if already_started_by_other_admin:
        raise HTTPException(
            status_code=409,
            detail="Another tenant admin started verification. Only the same admin must approve all documents."
        )

    # ✅ update document
    doc.verification_status = ApprovalStatusEnum.APPROVED if payload.approve else ApprovalStatusEnum.REJECTED
    doc.verified_by = session.user_id
    doc.verified_on = datetime.now(timezone.utc)

    # ✅ only if approved, check auto-approval
    fleet_auto_approved = False
    if payload.approve:
        fleet_auto_approved = auto_approve_fleet_if_ready(db, fleet)

    db.commit()

    return {
        "message": "Document verified successfully",
        "fleet_auto_approved": fleet_auto_approved
    }
