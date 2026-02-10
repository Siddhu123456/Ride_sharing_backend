from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.role_guard import require_role

from app.models.fleet import Fleet
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.commission_settlement import CommissionSettlement
from app.models.commission_settlement_trip import CommissionSettlementTrip

from app.schemas.enums import (
    TenantRoleEnum,
    WalletOwnerEnum,
    WalletTxnDirectionEnum,
    WalletTxnReasonEnum,
    SettlementStatusEnum
)
from app.schemas.fleet_settlement import (
    FleetSettlementResponse,
    FleetSettlementPayResponse
)
from app.models.user_session import UserSession

router = APIRouter(
    prefix="/fleet/settlements",
    tags=["Fleet - Commission Settlement"]
)


@router.get("/pending", response_model=list[FleetSettlementResponse])
def get_pending_settlements(
    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(TenantRoleEnum.FLEET_OWNER)
    )
):
    fleet = db.execute(
        select(Fleet).where(Fleet.owner_user_id == session.user_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(403, "Fleet not found")

    settlements = db.execute(
        select(CommissionSettlement)
        .where(
            CommissionSettlement.fleet_id == fleet.fleet_id,
            CommissionSettlement.status == SettlementStatusEnum.PENDING
        )
    ).scalars().all()

    response = []

    for s in settlements:
        trips = db.execute(
            select(CommissionSettlementTrip)
            .where(CommissionSettlementTrip.settlement_id == s.settlement_id)
        ).scalars().all()

        response.append(
            FleetSettlementResponse(
                settlement_id=s.settlement_id,
                total_commission=s.total_commission,
                status=s.status,
                created_on=s.created_on,
                paid_on=s.paid_on,
                trips=[
                    {
                        "trip_id": t.trip_id,
                        "commission_amount": t.commission_amount
                    }
                    for t in trips
                ]
            )
        )

    return response


@router.post("/{settlement_id}/pay", response_model=FleetSettlementPayResponse)
def pay_commission_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(TenantRoleEnum.FLEET_OWNER)
    )
):
    fleet = db.execute(
        select(Fleet).where(Fleet.owner_user_id == session.user_id)
    ).scalar_one_or_none()

    if not fleet:
        raise HTTPException(403, "Fleet not found")

    settlement = db.execute(
        select(CommissionSettlement)
        .where(
            CommissionSettlement.settlement_id == settlement_id,
            CommissionSettlement.fleet_id == fleet.fleet_id
        )
    ).scalar_one_or_none()

    if not settlement:
        raise HTTPException(404, "Settlement not found")

    if settlement.status != SettlementStatusEnum.PENDING:
        raise HTTPException(400, "Settlement already processed")

    fleet_wallet = db.execute(
        select(Wallet).where(
            Wallet.owner_type == WalletOwnerEnum.FLEET_OWNER,
            Wallet.owner_id == fleet.fleet_id
        )
    ).scalar_one()

    tenant_wallet = db.execute(
        select(Wallet).where(
            Wallet.owner_type == WalletOwnerEnum.TENANT,
            Wallet.owner_id == settlement.tenant_id
        )
    ).scalar_one()

    if fleet_wallet.balance < settlement.total_commission:
        raise HTTPException(400, "Insufficient wallet balance")

    # debit fleet wallet
    fleet_wallet.balance -= settlement.total_commission

    db.add(
        WalletTransaction(
            wallet_id=fleet_wallet.wallet_id,
            amount=settlement.total_commission,
            direction=WalletTxnDirectionEnum.DEBIT,
            reason=WalletTxnReasonEnum.COMMISSION_SETTLED
        )
    )

    # credit tenant wallet
    tenant_wallet.balance += settlement.total_commission

    db.add(
        WalletTransaction(
            wallet_id=tenant_wallet.wallet_id,
            amount=settlement.total_commission,
            direction=WalletTxnDirectionEnum.CREDIT,
            reason=WalletTxnReasonEnum.COMMISSION_SETTLED
        )
    )

    settlement.status = SettlementStatusEnum.COMPLETED
    settlement.paid_on = datetime.now(timezone.utc)

    db.commit()

    return FleetSettlementPayResponse(
        settlement_id=settlement.settlement_id,
        status=settlement.status,
        paid_on=settlement.paid_on
    )
