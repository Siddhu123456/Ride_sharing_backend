"""Compatibility shim.

Implementation moved to `app.schemas.fleet_owner.fleet_admin`.
This module re-exports admin schemas so existing imports continue to work.
"""

from app.schemas.fleet_owner.fleet_admin import (
    FleetPendingResponse,
    FleetApprovalRequest,
)

__all__ = ["FleetPendingResponse", "FleetApprovalRequest"]
