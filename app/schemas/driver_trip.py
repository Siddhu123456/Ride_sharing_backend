"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_trip import DriverTripListResponse``.
"""

from app.schemas.driver.driver_trip import ActiveTripResponse, DriverTripItem, DriverTripListResponse  # noqa: F401

__all__ = ["ActiveTripResponse", "DriverTripItem", "DriverTripListResponse"]
