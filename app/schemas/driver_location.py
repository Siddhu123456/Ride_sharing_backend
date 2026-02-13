"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_location import DriverLocationResponse``.
"""

from app.schemas.driver.driver_location import UpdateDriverLocationRequest, DriverLocationResponse  # noqa: F401

__all__ = ["UpdateDriverLocationRequest", "DriverLocationResponse"]
