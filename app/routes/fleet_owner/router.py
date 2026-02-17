from fastapi import APIRouter

from .fleet_owner import router as fleet_owner_router
from .fleet_owner_driver import router as fleet_owner_driver_router
from .fleet_owner_vehicle import router as fleet_owner_vehicle_router
from .fleet_owner_vehicle_assignment import router as fleet_owner_vehicle_assignment_router
from .fleet_settlement import router as fleet_settlement_router
from .fleet_overview_routes import router as fleet_overview_router

router = APIRouter()

router.include_router(fleet_owner_router)
router.include_router(fleet_owner_driver_router)
router.include_router(fleet_owner_vehicle_router)
router.include_router(fleet_owner_vehicle_assignment_router)
router.include_router(fleet_settlement_router)
router.include_router(fleet_overview_router)

__all__ = ["router"]
