from fastapi import APIRouter

from .admin_tenant import router as admin_tenant_router
from .admin_tenant_admin import router as admin_tenant_admin_router
from .admin_tenant_tax_rule import router as admin_tenant_tax_rule_router

router = APIRouter()

# Include subrouters in the files within this package.
router.include_router(admin_tenant_router)
router.include_router(admin_tenant_admin_router)
router.include_router(admin_tenant_tax_rule_router)

__all__ = ["router"]
