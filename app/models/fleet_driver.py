"""Compatibility shim.

Implementation moved to `app.models.fleet_owner.fleet_driver`.
This module re-exports the `FleetDriver` model so existing imports continue to work.
"""

from app.models.fleet_owner.fleet_driver import FleetDriver

__all__ = ["FleetDriver"]
