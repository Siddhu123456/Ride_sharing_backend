"""Compatibility shim.

Implementation moved to `app.models.fleet_owner.fleet_document`.
This module re-exports the `FleetDocument` model so existing imports continue to work.
"""

from app.models.fleet_owner.fleet_document import FleetDocument

__all__ = ["FleetDocument"]
