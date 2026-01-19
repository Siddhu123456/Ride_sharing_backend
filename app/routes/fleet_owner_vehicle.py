from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.deps import get_current_user_session
from app.models.user_session import UserSession

from app.models.fleet import Fleet
from app.models.vehicle import Vehicle
from app.models.vehicle_document import VehicleDocument

from app.schemas.vehicle_owner import VehicleCreateRequest, VehicleResponse
from app.schemas.vehicle_docs import (
    VehicleDocumentUploadRequest, VehicleDocumentResponse, VehicleDocStatusResponse
)

from app.services.vehicle_workflow import get_vehicle_docs, compute_vehicle_doc_status

router = APIRouter(prefix="/fleet-owner", tags=["Fleet Owner - Vehicles"])


# ✅ Create vehicle under fleet
@router.post("/fleets/{fleet_id}/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def add_vehicle_to_fleet(
    fleet_id: int,
    payload: VehicleCreateRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == fleet_id)).scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")

    if fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ 1 vehicle only in one fleet: registration_no is UNIQUE already
    existing = db.execute(
        select(Vehicle).where(Vehicle.registration_no == payload.registration_no)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Vehicle with this registration number already exists")

    vehicle = Vehicle(
        tenant_id=fleet.tenant_id,
        fleet_id=fleet_id,
        category=payload.category,
        registration_no=payload.registration_no,
        make=payload.make,
        model=payload.model,
        year_of_manufacture=payload.year_of_manufacture,
        created_by=session.user_id
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


# ✅ Upload vehicle document
@router.post("/vehicles/{vehicle_id}/documents", response_model=VehicleDocumentResponse, status_code=201)
def upload_vehicle_document(
    vehicle_id: int,
    payload: VehicleDocumentUploadRequest,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    vehicle = db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # ✅ ensure this vehicle belongs to fleet owned by session user
    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == vehicle.fleet_id)).scalar_one_or_none()
    if not fleet or fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ stop reupload same type (if constraint added)
    existing = db.execute(
        select(VehicleDocument).where(
            and_(
                VehicleDocument.vehicle_id == vehicle_id,
                VehicleDocument.document_type == payload.document_type
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="This document type already uploaded")

    doc = VehicleDocument(
        vehicle_id=vehicle_id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        created_by=session.user_id
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ✅ Fleet owner checks vehicle docs status
@router.get("/vehicles/{vehicle_id}/documents/status", response_model=VehicleDocStatusResponse)
def vehicle_doc_status(
    vehicle_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(get_current_user_session),
):
    vehicle = db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)).scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    fleet = db.execute(select(Fleet).where(Fleet.fleet_id == vehicle.fleet_id)).scalar_one_or_none()
    if not fleet or fleet.owner_user_id != session.user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    docs = get_vehicle_docs(db, vehicle_id)
    missing, all_uploaded, all_approved, approved_by_same_admin = compute_vehicle_doc_status(docs)

    return VehicleDocStatusResponse(
        vehicle_id=vehicle_id,
        uploaded=docs,
        missing=missing,
        all_uploaded=all_uploaded,
        all_approved=all_approved,
        approved_by_same_admin=approved_by_same_admin
    )
