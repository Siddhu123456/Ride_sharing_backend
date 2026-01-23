from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user import AppUser
from app.models.user_role import UserRole
from app.models.user_session import UserSession
from app.models.tenant import Tenant, TenantCountry
from app.models.fleet import Fleet
from app.models.fleet_document import FleetDocument

from app.schemas.admin_tenant import TenantResponse
from app.schemas.enums import FleetDocumentTypeEnum, TenantRoleEnum
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
from app.utils.file_storage import save_upload_file

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner Apply"])

# ✅ CHECK IF USER HAS A FLEET (For Redirect)
@router.get("/me", response_model=Optional[FleetApplyResponse])
def get_my_fleet(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session) # ✅ Validates Token
):
    # Check if this user ID exists in the fleet table
    fleet = db.execute(
        select(Fleet).where(Fleet.owner_user_id == session.user_id)
    ).scalar_one_or_none()
    
    if not fleet:
        # ✅ This 404 is EXPECTED for new applicants. 
        # The frontend will catch this and show the registration form.
        raise HTTPException(status_code=404, detail="No fleet found")
        
    return fleet


# ✅ LIST TENANTS (Filtered by User's Country)
@router.get("/tenants", response_model=List[TenantResponse])
def list_tenants_for_user(
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session)
):
    # 1. Get User's Country
    user = db.execute(
        select(AppUser).where(AppUser.user_id == session.user_id)
    ).scalar_one_or_none()
    
    if not user or not user.country_code:
        raise HTTPException(status_code=400, detail="User country not defined")

    # 2. Find Tenants operating in that country
    # Join Tenant -> TenantCountry where country_code matches user
    stmt = (
        select(Tenant)
        .join(TenantCountry, Tenant.tenant_id == TenantCountry.tenant_id)
        .where(TenantCountry.country_code == user.country_code)
    )
    
    tenants = db.execute(stmt).scalars().all()
    return tenants



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

    # ✅ create fleet application
    fleet = Fleet(
        tenant_id=payload.tenant_id,
        owner_user_id=session.user_id,
        fleet_name=payload.fleet_name,
        created_by=session.user_id
    )

    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    # ✅ assign FLEET_OWNER role immediately after apply
    role_exists = db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == session.user_id,
                UserRole.user_role == TenantRoleEnum.FLEET_OWNER,
                UserRole.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not role_exists:
        db.add(UserRole(
            user_id=session.user_id,
            user_role=TenantRoleEnum.FLEET_OWNER,
            is_active=True
        ))
        db.commit()

    return fleet


@router.post("/fleets/{fleet_id}/documents", response_model=FleetDocumentResponse, status_code=201)
def upload_fleet_document(
    fleet_id: int,
    document_type: FleetDocumentTypeEnum = Form(...),
    document_number: str | None = Form(None),
    file: UploadFile = File(...),
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
                FleetDocument.document_type == document_type
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="This document type is already uploaded")

    # ✅ store file
    stored_path = save_upload_file(file, folder=f"fleet_docs/{fleet_id}")

    doc = FleetDocument(
        fleet_id=fleet_id,
        document_type=document_type,
        file_url=stored_path,
        document_number=document_number,
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
