from fastapi import APIRouter

from .tenant_admin_fleet import router as tenant_fleet_router
from .tenant_admin_driver_verify import router as tenant_driver_verify_router
from .tenant_admin_tenant_setup_routes import router as tenant_setup_router
from .tenant_admin_vehicle_verify import router as tenant_vehicle_verify_router
from .tenant_settlement import router as tenant_settlement_router

router = APIRouter()

router.include_router(tenant_fleet_router)
router.include_router(tenant_driver_verify_router)
router.include_router(tenant_setup_router)
router.include_router(tenant_vehicle_verify_router)
router.include_router(tenant_settlement_router)

__all__ = ["router"]
