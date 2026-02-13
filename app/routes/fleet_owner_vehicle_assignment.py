"""Compatibility shim.

Implementation moved to `app.routes.fleet_owner.fleet_owner_vehicle_assignment`.
This file re-exports the router so older import paths continue to work.
"""

from app.routes.fleet_owner.fleet_owner_vehicle_assignment import router as router

__all__ = ["router"]

