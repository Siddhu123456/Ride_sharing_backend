from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timezone

from app.models.vehicle_document import VehicleDocument
from app.models.vehicle import Vehicle
from app.schemas.enums import VehicleDocumentTypeEnum, ApprovalStatusEnum, VehicleStatusEnum

REQUIRED_VEHICLE_DOCS = {
    VehicleDocumentTypeEnum.INSURANCE,
    VehicleDocumentTypeEnum.REGISTRATION,
}

def get_vehicle_docs(db: Session, vehicle_id: int):
    return db.execute(
        select(VehicleDocument).where(VehicleDocument.vehicle_id == vehicle_id)
    ).scalars().all()

def compute_vehicle_doc_status(docs: list[VehicleDocument]):
    uploaded_types = {d.document_type for d in docs}
    missing = list(REQUIRED_VEHICLE_DOCS - uploaded_types)

    all_uploaded = len(missing) == 0
    all_approved = all_uploaded and all(d.verification_status == ApprovalStatusEnum.APPROVED for d in docs)

    verified_by_set = {d.verified_by for d in docs if d.verified_by is not None}
    approved_by_same_admin = all_approved and len(verified_by_set) == 1

    return missing, all_uploaded, all_approved, approved_by_same_admin

def auto_approve_vehicle_if_ready(db: Session, vehicle: Vehicle):
    docs = get_vehicle_docs(db, vehicle.vehicle_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_vehicle_doc_status(docs)

    if not (all_uploaded and all_approved and approved_by_same_admin):
        return False

    # ✅ vehicle approved
    vehicle.approval_status = ApprovalStatusEnum.APPROVED
    vehicle.status = VehicleStatusEnum.ACTIVE
    vehicle.verified_by = docs[0].verified_by
    vehicle.verified_on = datetime.now(timezone.utc)

    return True
