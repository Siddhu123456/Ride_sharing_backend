from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum, ApprovalStatusEnum

from app.models.user_session import UserSession
from app.models.tenant_admin import TenantAdmin
from app.models.vehicle import Vehicle
from app.models.vehicle_document import VehicleDocument

from app.schemas.fleet_verify import VerifyFleetDocumentRequest  # reuse schema {approve: bool}
from app.schemas.vehicle_docs import VehicleDocumentResponse
from app.services.vehicle_workflow import (
    get_vehicle_docs,
    compute_vehicle_doc_status,
    auto_approve_vehicle_if_ready
)

router = APIRouter(prefix="/tenant-admin/vehicles", tags=["Tenant Admin - Vehicle Verification"])


# ✅ List pending vehicles
@router.get("/pending", response_model=List[int])
def list_pending_vehicles(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)).scalar_one_or_none()
    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    vehicles = db.execute(
        select(Vehicle).where(
            and_(
                Vehicle.tenant_id == tenant_admin.tenant_id,
                Vehicle.approval_status == ApprovalStatusEnum.PENDING
            )
        )
    ).scalars().all()

    # return vehicle_ids (or create response model)
    return [v.vehicle_id for v in vehicles]


# ✅ Get vehicle documents
@router.get("/{vehicle_id}/documents", response_model=List[VehicleDocumentResponse])
def get_vehicle_documents(
    vehicle_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)).scalar_one_or_none()
    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    vehicle = db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    docs = db.execute(
        select(VehicleDocument).where(VehicleDocument.vehicle_id == vehicle_id)
    ).scalars().all()

    return docs


# ✅ Verify vehicle document
@router.post("/documents/{document_id}/verify", status_code=200)
def verify_vehicle_document(
    document_id: int,
    payload: VerifyFleetDocumentRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN)),
):
    tenant_admin = db.execute(select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)).scalar_one_or_none()
    if not tenant_admin:
        raise HTTPException(status_code=403, detail="Not a tenant admin")

    doc = db.execute(
        select(VehicleDocument).where(VehicleDocument.document_id == document_id)
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Vehicle document not found")

    vehicle = db.execute(select(Vehicle).where(Vehicle.vehicle_id == doc.vehicle_id)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if vehicle.tenant_id != tenant_admin.tenant_id:
        raise HTTPException(status_code=403, detail="Not allowed for this tenant")

    # ✅ must upload both docs before verification
    docs = get_vehicle_docs(db, vehicle.vehicle_id)
    missing, all_uploaded, _, _ = compute_vehicle_doc_status(docs)

    if not all_uploaded:
        raise HTTPException(
            status_code=400,
            detail=f"All required vehicle documents must be uploaded before verification. Missing: {missing}"
        )

    # ✅ same tenant admin rule
    started_by_other_admin = any(
        d.verified_by is not None and d.verified_by != session.user_id
        for d in docs
    )
    if started_by_other_admin:
        raise HTTPException(
            status_code=409,
            detail="Another tenant admin started verification. Same admin must approve all docs."
        )

    # ✅ verify doc
    doc.verification_status = ApprovalStatusEnum.APPROVED if payload.approve else ApprovalStatusEnum.REJECTED
    doc.verified_by = session.user_id
    doc.verified_on = datetime.now(timezone.utc)

    vehicle_auto_approved = False
    if payload.approve:
        vehicle_auto_approved = auto_approve_vehicle_if_ready(db, vehicle)

    db.commit()

    return {
        "message": "Vehicle document verified successfully",
        "vehicle_auto_approved": vehicle_auto_approved
    }
