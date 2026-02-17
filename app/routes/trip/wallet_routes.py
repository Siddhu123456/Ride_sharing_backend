from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_guard import require_role

from app.models.fleet_owner.fleet import Fleet
from app.models.tenant.tenant_admin import TenantAdmin
from app.models.trip.wallet import Wallet
from app.models.trip.wallet_transaction import WalletTransaction
from app.models.common.user_session import UserSession

from app.schemas.enums import TenantRoleEnum, WalletOwnerEnum
from app.schemas.trip import (
    WalletResponse,
    WalletTransactionItem,
    WalletTransactionListResponse
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])



@router.get("/me", response_model=WalletResponse)
def get_my_wallet(
    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(
            TenantRoleEnum.TENANT_ADMIN,
            TenantRoleEnum.FLEET_OWNER
        )
    )
):
    if session.active_role == TenantRoleEnum.TENANT_ADMIN:
        tenant_admin = db.execute(
            select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
        ).scalar_one_or_none()

        if not tenant_admin:
            raise HTTPException(403, "Tenant not found")

        owner_type = WalletOwnerEnum.TENANT
        owner_id = tenant_admin.tenant_id

    else:  # FLEET_OWNER
        fleet = db.execute(
            select(Fleet).where(Fleet.owner_user_id == session.user_id)
        ).scalar_one_or_none()

        if not fleet:
            raise HTTPException(403, "Fleet not found")

        owner_type = WalletOwnerEnum.FLEET_OWNER
        owner_id = fleet.fleet_id

    wallet = db.execute(
        select(Wallet).where(
            Wallet.owner_type == owner_type,
            Wallet.owner_id == owner_id
        )
    ).scalar_one_or_none()

    if not wallet:
        raise HTTPException(404, "Wallet not found")

    return wallet


@router.get("/transactions", response_model=WalletTransactionListResponse)
def get_wallet_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),

    db: Session = Depends(get_db),
    session: UserSession = Depends(
        require_role(
            TenantRoleEnum.TENANT_ADMIN,
            TenantRoleEnum.FLEET_OWNER
        )
    )
):
    offset = (page - 1) * limit

    # -------------------------------------------------
    # Resolve owner
    # -------------------------------------------------
    if session.active_role == TenantRoleEnum.TENANT_ADMIN:
        tenant_admin = db.execute(
            select(TenantAdmin).where(TenantAdmin.user_id == session.user_id)
        ).scalar_one_or_none()

        if not tenant_admin:
            raise HTTPException(403, "Tenant not found")

        owner_type = WalletOwnerEnum.TENANT
        owner_id = tenant_admin.tenant_id

    else:  # FLEET_OWNER
        fleet = db.execute(
            select(Fleet).where(Fleet.owner_user_id == session.user_id)
        ).scalar_one_or_none()

        if not fleet:
            raise HTTPException(403, "Fleet not found")

        owner_type = WalletOwnerEnum.FLEET_OWNER
        owner_id = fleet.fleet_id

    # -------------------------------------------------
    # Wallet
    # -------------------------------------------------
    wallet = db.execute(
        select(Wallet).where(
            Wallet.owner_type == owner_type,
            Wallet.owner_id == owner_id
        )
    ).scalar_one_or_none()

    if not wallet:
        raise HTTPException(404, "Wallet not found")

    # -------------------------------------------------
    # Transactions
    # -------------------------------------------------
    transactions = db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.wallet_id)
        .order_by(desc(WalletTransaction.created_on))
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    total = db.execute(
        select(func.count())
        .select_from(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.wallet_id)
    ).scalar()

    return WalletTransactionListResponse(
        wallet_id=wallet.wallet_id,
        owner_type=wallet.owner_type,
        owner_id=wallet.owner_id,
        balance=wallet.balance,

        transactions=[
            WalletTransactionItem.model_validate(tx)
            for tx in transactions
        ],

        page=page,
        limit=limit,
        total=total
    )
