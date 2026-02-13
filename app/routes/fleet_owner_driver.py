"""Compatibility shim.

Implementation moved to `app.routes.fleet_owner.fleet_owner_driver`.
This module keeps a thin shim so existing imports like
`from app.routes.fleet_owner_driver import router` keep working.
"""

from app.routes.fleet_owner.fleet_owner_driver import router as router

__all__ = ["router"]
