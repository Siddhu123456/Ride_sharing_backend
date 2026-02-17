from fastapi import APIRouter

from .driver_vehicle_routes import router as driver_vehicle_router
from .driver_docs import router as driver_docs_router
from .driver_shift_location import router as driver_shift_location_router
from .driver_profile_routes import router as driver_profile_router
from .driver_trip_routes import router as driver_trip_router
from .driver_dashboard_routes import router as driver_dashboard_router
from .driver_offer_routes import router as driver_offer_router

router = APIRouter()

# Include subrouters in the files within this package.
router.include_router(driver_vehicle_router)
router.include_router(driver_docs_router)
router.include_router(driver_shift_location_router)
router.include_router(driver_profile_router)
router.include_router(driver_trip_router)
router.include_router(driver_dashboard_router)
router.include_router(driver_offer_router)

__all__ = ["router"]
