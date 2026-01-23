from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.fleet import Fleet
from app.models.fleet_document import FleetDocument
from app.models.user_role import UserRole
from app.schemas.enums import (
    FleetDocumentTypeEnum,
    ApprovalStatusEnum,
    AccountStatusEnum,
    TenantRoleEnum,
)


REQUIRED_DOC_TYPES = {
    FleetDocumentTypeEnum.AADHAAR,
    FleetDocumentTypeEnum.PAN,
    FleetDocumentTypeEnum.GST_CERTIFICATE,
    FleetDocumentTypeEnum.BUSINESS_REGISTRATION,
}


def get_fleet_uploaded_docs(db: Session, fleet_id: int):
    return db.execute(
        select(FleetDocument).where(FleetDocument.fleet_id == fleet_id)
    ).scalars().all()


def compute_doc_status(uploaded_docs: list[FleetDocument]):
    uploaded_types = {d.document_type for d in uploaded_docs}
    missing = list(REQUIRED_DOC_TYPES - uploaded_types)

    all_uploaded = len(missing) == 0
    all_approved = (
        all_uploaded and all(d.verification_status == ApprovalStatusEnum.APPROVED for d in uploaded_docs)
    )

    # approved_by_same_admin means all docs verified_by is same value (not null)
    verified_by_values = {d.verified_by for d in uploaded_docs if d.verified_by is not None}
    approved_by_same_admin = all_approved and len(verified_by_values) == 1

    return missing, all_uploaded, all_approved, approved_by_same_admin


def auto_approve_fleet_if_ready(db: Session, fleet: Fleet):
    """
    Called after every document verification.
    If all 4 docs approved by same tenant admin => approve fleet.
    """
    uploaded_docs = get_fleet_uploaded_docs(db, fleet.fleet_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_doc_status(uploaded_docs)

    if not (all_uploaded and all_approved and approved_by_same_admin):
        return False

    approving_admin_user_id = uploaded_docs[0].verified_by

    fleet.approval_status = ApprovalStatusEnum.APPROVED
    fleet.status = AccountStatusEnum.ACTIVE
    fleet.verified_by = approving_admin_user_id
    fleet.verified_on = datetime.now(timezone.utc)

    return True
