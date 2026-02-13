"""Compatibility shim: re-export driver models from the driver package.

Preserves imports like ``from app.models.driver_location import DriverLocation``.
"""

from app.models.driver.driver_location import DriverLocation  # noqa: F401

__all__ = ["DriverLocation"]
