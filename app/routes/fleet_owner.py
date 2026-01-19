from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession
from app.models.tenant import Tenant
from app.models.fleet import Fleet
from app.models.fleet_document import FleetDocument

from app.schemas.fleet_owner_apply import (
    FleetApplyRequest, FleetApplyResponse
)
from app.schemas.fleet_docs import (
    FleetDocumentUploadRequest, FleetDocumentResponse, FleetDocumentStatusResponse
)
from app.services.fleet_workflow import (
    get_fleet_uploaded_docs,
    compute_doc_status
)

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner Apply"])


# ✅ Apply for Fleet Owner under a tenant
@router.post("/apply", response_model=FleetApplyResponse, status_code=status.HTTP_201_CREATED)
def apply_fleet_owner(
    payload: FleetApplyRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    # ✅ tenant must exist
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == payload.tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # ✅ prevent duplicate fleet application for same tenant + user
    existing = db.execute(
        select(Fleet).where(
            and_(
                Fleet.tenant_id == payload.tenant_id,
                Fleet.owner_user_id == session.user_id
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Fleet application already exists")

    fleet = Fleet(
        tenant_id=payload.tenant_id,
        owner_user_id=session.user_id,
        fleet_name=payload.fleet_name,
        created_by=session.user_id
    )

    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


# ✅ Upload Fleet Document (one per type)
@router.post("/fleets/{fleet_id}/documents", response_model=FleetDocumentResponse, status_code=201)
def upload_fleet_document(
    fleet_id: int,
    payload: FleetDocumentUploadRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    fleet = db.execute(
        select(Fleet).where(Fleet.fleet_id == fleet_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ stop re-upload same document type
    existing = db.execute(
        select(FleetDocument).where(
            and_(
                FleetDocument.fleet_id == fleet_id,
                FleetDocument.document_type == payload.document_type
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="This document type is already uploaded")

    doc = FleetDocument(
        fleet_id=fleet_id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        document_number=payload.document_number,
        created_by=session.user_id
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ✅ User sees what's uploaded + what's missing (Frontend uses this)
@router.get("/fleets/{fleet_id}/documents/status", response_model=FleetDocumentStatusResponse)
def get_document_status(
    fleet_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    fleet = db.execute(
        select(Fleet).where(Fleet.fleet_id == fleet_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    uploaded_docs = get_fleet_uploaded_docs(db, fleet_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_doc_status(uploaded_docs)

    return FleetDocumentStatusResponse(
        fleet_id=fleet_id,
        uploaded=uploaded_docs,
        missing=missing,
        all_uploaded=all_uploaded,
        all_approved=all_approved,
        approved_by_same_admin=approved_by_same_admin
    )
