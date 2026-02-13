"""Compatibility shim.

Implementation moved to `app.schemas.fleet_owner.fleet_vehicle_assignment`.
This module re-exports assignment schemas so existing imports continue to work.
"""

from app.schemas.fleet_owner.fleet_vehicle_assignment import (
    FleetAssignDriverToVehicleRequest,
    FleetAssignDriverToVehicleResponse,
)

__all__ = [
    "FleetAssignDriverToVehicleRequest",
    "FleetAssignDriverToVehicleResponse",
]
