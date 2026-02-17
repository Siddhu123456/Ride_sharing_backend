from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.common.user_session import UserSession

from app.models.driver.driver_profile import DriverProfile
from app.models.driver.driver_document import DriverDocument

from app.schemas.driver import (
    DriverDocumentResponse,
    DriverDocumentStatusResponse
)

from app.services.driver.driver_workflow import (
    get_uploaded_driver_docs,
    compute_driver_doc_status
)

from app.utils.file_storage import save_upload_file


router = APIRouter(prefix="/driver", tags=["Driver - Documents"])

from app.schemas.enums import ApprovalStatusEnum, DriverDocumentTypeEnum


@router.post(
    "/documents",
    response_model=DriverDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def upload_driver_document(
    document_type: DriverDocumentTypeEnum = Form(...),
    document_number: Optional[str] = Form(None),
    expiry_date: Optional[date] = Form(None),
    file: UploadFile = File(...),

    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    # driver profile must exist
    profile = db.execute(
        select(DriverProfile)
        .where(DriverProfile.driver_id == session.user_id)
    ).scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Driver profile not created yet"
        )

    # check existing document
    existing_doc = db.execute(
        select(DriverDocument).where(
            and_(
                DriverDocument.driver_id == session.user_id,
                DriverDocument.document_type == document_type
            )
        )
    ).scalar_one_or_none()

    # approved documents cannot be re-uploaded
    if (
        existing_doc
        and existing_doc.verification_status == ApprovalStatusEnum.APPROVED
    ):
        raise HTTPException(
            status_code=400,
            detail="Approved document cannot be re-uploaded"
        )

    # save file
    folder = f"driver_docs/{session.user_id}"
    file_url = save_upload_file(file, folder)

    # re-upload (PENDING or REJECTED)
    if existing_doc:
        existing_doc.file_url = file_url
        existing_doc.document_number = document_number
        existing_doc.expiry_date = expiry_date
        existing_doc.verification_status = ApprovalStatusEnum.PENDING
        existing_doc.created_by = session.user_id

        db.commit()
        db.refresh(existing_doc)
        return existing_doc

    # first-time upload
    doc = DriverDocument(
        driver_id=session.user_id,
        document_type=document_type,
        file_url=file_url,
        document_number=document_number,
        expiry_date=expiry_date,
        verification_status=ApprovalStatusEnum.PENDING,
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
