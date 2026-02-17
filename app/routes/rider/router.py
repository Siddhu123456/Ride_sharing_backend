from fastapi import APIRouter

from .rider_routes import router as rider_router
from .rider_trip_routes import router as rider_trip_router

router = APIRouter()

router.include_router(rider_router)
router.include_router(rider_trip_router)

__all__ = ["router"]
