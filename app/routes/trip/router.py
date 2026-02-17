from fastapi import APIRouter

from .trip_routes import router as trip_router
from .trip_fare_routes import router as trip_fare_router
from .trip_lifecycle_routes import router as trip_lifecycle_router
from .trip_navigation_routes import router as trip_navigation_router
from .otp_routes import router as otp_router
from .wallet_routes import router as wallet_router

router = APIRouter()

router.include_router(trip_router)
router.include_router(trip_fare_router)
router.include_router(trip_lifecycle_router)
router.include_router(trip_navigation_router)
router.include_router(otp_router)
router.include_router(wallet_router)

__all__ = ["router"]
