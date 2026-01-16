from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from starlette import status

from app.core.database import get_db
from app.core.admin_auth import verify_admin

from app.models.tenant import Tenant
from app.models.user import AppUser
from app.models.tenant_admin import TenantAdmin
from app.models.user_role import UserRole
from app.schemas.enums import UserRoleEnum

from app.schemas.tenant_admin import (
    AssignTenantAdminRequest,
    TenantAdminResponse,
    TenantAdminListResponse,
    RemoveTenantAdminResponse,
)

router = APIRouter(prefix="/admin/tenants", tags=["Admin Tenant Admins"])


# =========================================================
# ✅ 1) ASSIGN TENANT ADMIN
# POST /admin/tenants/{tenant_id}/admins
# =========================================================
@router.post(
    "/{tenant_id}/admins",
    response_model=TenantAdminResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin)]
)
def assign_tenant_admin(
    tenant_id: int,
    payload: AssignTenantAdminRequest,
    db: Session = Depends(get_db)
):
    # ✅ Tenant must exist
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # ✅ User must exist
    user = db.execute(
        select(AppUser).where(AppUser.user_id == payload.user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Check already assigned
    existing_admin = db.execute(
        select(TenantAdmin).where(
            and_(
                TenantAdmin.tenant_id == tenant_id,
                TenantAdmin.user_id == payload.user_id
            )
        )
    ).scalar_one_or_none()

    # ✅ If exists but inactive -> reactivate
    if existing_admin:
        if existing_admin.status != "ACTIVE":
            existing_admin.status = "ACTIVE"
            existing_admin.is_primary = payload.is_primary
            db.commit()
            db.refresh(existing_admin)
            return existing_admin

        raise HTTPException(status_code=400, detail="User is already a tenant admin")

    # ✅ If assigning primary admin: unset existing primary
    if payload.is_primary:
        primary_admin = db.execute(
            select(TenantAdmin).where(
                and_(
                    TenantAdmin.tenant_id == tenant_id,
                    TenantAdmin.is_primary == True,
                    TenantAdmin.status == "ACTIVE"
                )
            )
        ).scalar_one_or_none()

        if primary_admin:
            primary_admin.is_primary = False

    # ✅ Create new tenant_admin row
    tenant_admin = TenantAdmin(
        tenant_id=tenant_id,
        user_id=payload.user_id,
        is_primary=payload.is_primary,
        status="ACTIVE"
    )
    db.add(tenant_admin)

    # ✅ Ensure role exists in user_roles as TENANT_ADMIN
    role_exists = db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == payload.user_id,
                UserRole.user_role == UserRoleEnum.TENANT_ADMIN,
                UserRole.is_active == True
            )
        )
    ).scalar_one_or_none()

    if not role_exists:
        new_role = UserRole(
            user_id=payload.user_id,
            user_role=UserRoleEnum.TENANT_ADMIN,
            is_active=True
        )
        db.add(new_role)

    db.commit()
    db.refresh(tenant_admin)

    return tenant_admin


# =========================================================
# ✅ 2) LIST TENANT ADMINS
# GET /admin/tenants/{tenant_id}/admins
# =========================================================
@router.get(
    "/{tenant_id}/admins",
    response_model=TenantAdminListResponse,
    dependencies=[Depends(verify_admin)]
)
def list_tenant_admins(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    # ✅ Tenant must exist
    tenant = db.execute(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    admins = db.execute(
        select(TenantAdmin).where(TenantAdmin.tenant_id == tenant_id)
    ).scalars().all()

    return TenantAdminListResponse(tenant_id=tenant_id, admins=admins)


# =========================================================
# ✅ 3) REMOVE TENANT ADMIN (SOFT DELETE)
# DELETE /admin/tenants/{tenant_id}/admins/{user_id}
# =========================================================
@router.delete(
    "/{tenant_id}/admins/{user_id}",
    response_model=RemoveTenantAdminResponse,
    dependencies=[Depends(verify_admin)]
)
def remove_tenant_admin(
    tenant_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    admin_row = db.execute(
        select(TenantAdmin).where(
            and_(
                TenantAdmin.tenant_id == tenant_id,
                TenantAdmin.user_id == user_id
            )
        )
    ).scalar_one_or_none()

    if not admin_row:
        raise HTTPException(status_code=404, detail="Tenant admin not found")

    # ✅ Soft delete
    admin_row.status = "INACTIVE"
    admin_row.is_primary = False

    db.commit()

    return {"message": "Tenant admin removed (set to INACTIVE)"}
