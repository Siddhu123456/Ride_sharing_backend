"""Compatibility shim for fleet overview routes.

Implementation moved to `app.routes.fleet_owner.fleet_overview`.
This shim re-exports the router so existing imports continue to work while
we keep the fleet-owner domain grouped.
"""

from app.routes.fleet_owner.fleet_overview import router as router

__all__ = ["router"]
