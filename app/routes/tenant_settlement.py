from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.role_guard import require_role

from app.models.tenant_admin import TenantAdmin
from app.models.trip import Trip
from app.models.commission_settlement import CommissionSettlement
from app.models.commission_settlement_trip import CommissionSettlementTrip

from app.models.vehicle import Vehicle
from app.schemas.enums import (
    TenantRoleEnum,
    SettlementStatusEnum
)
from app.schemas.tenant_settlement import (
    TenantSettlementCreateResponse,
    TenantSettlementDetailResponse
)
from app.models.user_session import UserSession

router = APIRouter(
    prefix="/tenant/settlements",
    tags=["Tenant - Commission Settlement"]
)


@router.post(
    "/fleet/{fleet_id}",
    response_model=TenantSettlementCreateResponse
)
def create_settlement_for_fleet(
    fleet_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN))
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(403, "Tenant admin not found")

    # 1 Calculate total unpaid commission
    total_commission = db.execute(
        select(func.coalesce(func.sum(Trip.platform_fee), 0))
        .select_from(Trip)
        .join(Vehicle, Vehicle.vehicle_id == Trip.vehicle_id)
        .outerjoin(
            CommissionSettlementTrip,
            CommissionSettlementTrip.trip_id == Trip.trip_id
        )
        .where(
            Trip.status == "COMPLETED",
            Trip.tenant_id == tenant_admin.tenant_id,
            Vehicle.fleet_id == fleet_id,
            CommissionSettlementTrip.trip_id.is_(None)
        )
    ).scalar()

    if total_commission == 0:
        raise HTTPException(400, "No unpaid trips for this fleet")

    # Create settlement header
    settlement = CommissionSettlement(
        tenant_id=tenant_admin.tenant_id,
        fleet_id=fleet_id,
        total_commission=total_commission,
        status=SettlementStatusEnum.PENDING
    )

    db.add(settlement)
    db.flush()

    # Lock trips into settlement
    trips = db.execute(
        select(Trip)
        .join(Vehicle, Vehicle.vehicle_id == Trip.vehicle_id)
        .outerjoin(
            CommissionSettlementTrip,
            CommissionSettlementTrip.trip_id == Trip.trip_id
        )
        .where(
            Trip.status == "COMPLETED",
            Trip.tenant_id == tenant_admin.tenant_id,
            Vehicle.fleet_id == fleet_id,
            CommissionSettlementTrip.trip_id.is_(None)
        )
    ).scalars().all()

    for trip in trips:
        db.add(
            CommissionSettlementTrip(
                settlement_id=settlement.settlement_id,
                trip_id=trip.trip_id,
                commission_amount=trip.platform_fee
            )
        )

    db.commit()

    return TenantSettlementCreateResponse(
        settlement_id=settlement.settlement_id,
        fleet_id=fleet_id,
        total_commission=settlement.total_commission,
        status=settlement.status,
        created_on=settlement.created_on
    )



@router.get(
    "/{settlement_id}",
    response_model=TenantSettlementDetailResponse
)
def get_settlement_details(
    settlement_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(TenantRoleEnum.TENANT_ADMIN)
    )
):
    tenant_admin = db.execute(
        select(TenantAdmin).where(
            TenantAdmin.user_id == session.user_id
        )
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(403, "Tenant admin not found")

    settlement = db.execute(
        select(CommissionSettlement)
        .where(
            CommissionSettlement.settlement_id == settlement_id,
            CommissionSettlement.tenant_id == tenant_admin.tenant_id
        )
    ).scalar_one_or_none()

    if not settlement:
        raise HTTPException(404, "Settlement not found")

    trips = db.execute(
        select(CommissionSettlementTrip)
        .where(
            CommissionSettlementTrip.settlement_id == settlement_id
        )
    ).scalars().all()

    return TenantSettlementDetailResponse(
        settlement_id=settlement.settlement_id,
        fleet_id=settlement.fleet_id,
        total_commission=settlement.total_commission,
        status=settlement.status,
        created_on=settlement.created_on,
        paid_on=settlement.paid_on,
        trips=[
            {
                "trip_id": t.trip_id,
                "commission_amount": t.commission_amount
            }
            for t in trips
        ]
    )
