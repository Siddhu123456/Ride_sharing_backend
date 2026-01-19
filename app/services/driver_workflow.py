from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timezone

from app.models.driver_document import DriverDocument
from app.models.driver_profile import DriverProfile
from app.models.fleet_driver import FleetDriver
from app.schemas.enums import DriverDocumentTypeEnum, ApprovalStatusEnum

REQUIRED_DRIVER_DOCS = {
    DriverDocumentTypeEnum.DRIVING_LICENSE,
    DriverDocumentTypeEnum.AADHAAR,
    DriverDocumentTypeEnum.PAN,
}


def get_uploaded_driver_docs(db: Session, driver_id: int):
    return db.execute(
        select(DriverDocument).where(DriverDocument.driver_id == driver_id)
    ).scalars().all()


def compute_driver_doc_status(docs: list[DriverDocument]):
    uploaded_types = {d.document_type for d in docs}
    missing = list(REQUIRED_DRIVER_DOCS - uploaded_types)

    all_uploaded = len(missing) == 0
    all_approved = all_uploaded and all(
        d.verification_status == ApprovalStatusEnum.APPROVED for d in docs
    )

    verified_by_set = {d.verified_by for d in docs if d.verified_by is not None}
    approved_by_same_admin = all_approved and len(verified_by_set) == 1

    return missing, all_uploaded, all_approved, approved_by_same_admin


def auto_approve_driver_if_ready(db: Session, driver_id: int):
    docs = get_uploaded_driver_docs(db, driver_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_driver_doc_status(docs)

    if not (all_uploaded and all_approved and approved_by_same_admin):
        return False

    # ✅ approve driver profile
    profile = db.execute(
        select(DriverProfile).where(DriverProfile.driver_id == driver_id)
    ).scalar_one_or_none()

    if profile:
        profile.approval_status = ApprovalStatusEnum.APPROVED
        profile.updated_on = datetime.now(timezone.utc)

    # ✅ approve fleet_driver mapping
    fleet_driver = db.execute(
        select(FleetDriver).where(
            and_(
                FleetDriver.driver_id == driver_id,
                FleetDriver.end_date.is_(None)
            )
        )
    ).scalar_one_or_none()

    if fleet_driver:
        fleet_driver.approval_status = ApprovalStatusEnum.APPROVED

    return True
