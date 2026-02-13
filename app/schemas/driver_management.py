"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_management import PendingDriverResponse``.
"""

from app.schemas.driver.driver_management import AddDriverToFleetByEmailRequest, FleetDriverResponse, PendingDriverResponse  # noqa: F401

__all__ = [
    "AddDriverToFleetByEmailRequest",
    "FleetDriverResponse",
    "PendingDriverResponse",
]