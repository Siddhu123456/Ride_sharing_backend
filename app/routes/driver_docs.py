from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession

from app.models.driver_profile import DriverProfile
from app.models.driver_document import DriverDocument

from app.schemas.driver_docs import (
    DriverDocumentUploadRequest,
    DriverDocumentResponse,
    DriverDocumentStatusResponse
)

from app.services.driver_workflow import (
    get_uploaded_driver_docs,
    compute_driver_doc_status
)

router = APIRouter(prefix="/driver", tags=["Driver - Documents"])


@router.post("/documents", response_model=DriverDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_driver_document(
    payload: DriverDocumentUploadRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    # ✅ driver profile must exist
    profile = db.execute(
        select(DriverProfile).where(DriverProfile.driver_id == session.user_id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=400, detail="Driver profile not created yet")

    existing = db.execute(
        select(DriverDocument).where(
            and_(
                DriverDocument.driver_id == session.user_id,
                DriverDocument.document_type == payload.document_type
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="This document type already uploaded")

    doc = DriverDocument(
        driver_id=session.user_id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        document_number=payload.document_number,
        expiry_date=payload.expiry_date,
        created_by=session.user_id
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documents/status", response_model=DriverDocumentStatusResponse)
def driver_document_status(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    uploaded_docs = get_uploaded_driver_docs(db, session.user_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_driver_doc_status(uploaded_docs)

    return DriverDocumentStatusResponse(
        driver_id=session.user_id,
        uploaded=uploaded_docs,
        missing=missing,
        all_uploaded=all_uploaded,
        all_approved=all_approved,
        approved_by_same_admin=approved_by_same_admin
    )
