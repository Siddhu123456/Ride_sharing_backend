# app/core/tenant_admin_guard.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.role_guard import require_role
from app.schemas.enums import TenantRoleEnum
from app.models.user_session import UserSession
from app.models.tenant_admin import TenantAdmin


def get_tenant_admin(
    db: Session = Depends(get_db),
    session: UserSession = Depends(require_role(TenantRoleEnum.TENANT_ADMIN))
) -> TenantAdmin:
    """
    ✅ Ensures:
    - JWT is valid
    - active_role is TENANT_ADMIN
    - TenantAdmin record exists
    - TenantAdmin is active
    """

    tenant_admin = db.execute(
        select(TenantAdmin).where(
            and_(
                TenantAdmin.user_id == session.user_id,
                TenantAdmin.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active tenant admin"
        )

    return tenant_admin
