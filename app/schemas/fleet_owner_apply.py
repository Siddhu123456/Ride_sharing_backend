"""Compatibility shim.

Implementation moved to `app.schemas.fleet_owner.fleet_owner_apply`.
This module re-exports the fleet-apply schemas so existing imports continue to work.
"""

from app.schemas.fleet_owner.fleet_owner_apply import FleetApplyRequest, FleetApplyResponse

__all__ = ["FleetApplyRequest", "FleetApplyResponse"]

