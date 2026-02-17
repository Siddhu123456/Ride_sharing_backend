from fastapi import APIRouter

from .auth import router as auth_router
from .country import router as country_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(country_router)

__all__ = ["router"]
