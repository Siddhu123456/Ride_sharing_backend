from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession

from app.models.driver_profile import DriverProfile
from app.models.driver_document import DriverDocument

from app.schemas.driver_docs import (
    DriverDocumentResponse,
    DriverDocumentStatusResponse
)

from app.services.driver_workflow import (
    get_uploaded_driver_docs,
    compute_driver_doc_status
)

from app.utils.file_storage import save_upload_file


router = APIRouter(prefix="/driver", tags=["Driver - Documents"])


@router.post(
    "/documents",
    response_model=DriverDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def upload_driver_document(
    document_type: str = Form(...),
    document_number: Optional[str] = Form(None),
    expiry_date: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    # ✅ driver profile must exist
    profile = db.execute(
        select(DriverProfile).where(
            DriverProfile.driver_id == session.user_id
        )
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Driver profile not created yet"
        )

    # ❌ prevent duplicate document upload
    existing = db.execute(
        select(DriverDocument).where(
            and_(
                DriverDocument.driver_id == session.user_id,
                DriverDocument.document_type == document_type
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This document type already uploaded"
        )

    # ✅ save file locally
    # example folder: driver_docs/<driver_id>
    folder = f"driver_docs/{session.user_id}"
    file_url = save_upload_file(file, folder)

    # ✅ save DB record
    doc = DriverDocument(
        driver_id=session.user_id,
        document_type=document_type,
        file_url=file_url,
        document_number=document_number,
        expiry_date=expiry_date,
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
