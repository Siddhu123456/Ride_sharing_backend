"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_profile import DriverProfileResponse``.
"""

from app.schemas.driver.driver_profile import DriverProfileResponse  # noqa: F401

__all__ = ["DriverProfileResponse"]
