"""Compatibility shim.

Implementation moved to `app.routes.fleet_owner.fleet_owner_vehicle`.
This shim re-exports the router to preserve existing import paths.
"""

from app.routes.fleet_owner.fleet_owner_vehicle import router as router

__all__ = ["router"]
