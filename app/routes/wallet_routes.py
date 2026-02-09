from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum
from app.schemas.wallet import WalletResponse
from app.models.wallet import Wallet
from app.models.user_session import UserSession

router = APIRouter(prefix="/wallet", tags=["Wallet"])

@router.get("/me", response_model=WalletResponse)
def get_my_wallet(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(
        TenantRoleEnum.TENANT_ADMIN,
        TenantRoleEnum.FLEET_OWNER
    ))
):
    wallet = db.query(Wallet).filter_by(
        owner_id=session.user_id
    ).first()

    return wallet
