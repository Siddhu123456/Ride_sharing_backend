"""Compatibility shim: re-export driver models from the driver package.

Preserves imports like ``from app.models.driver_location_history import DriverLocationHistory``.
"""

from app.models.driver.driver_location_history import DriverLocationHistory  # noqa: F401

__all__ = ["DriverLocationHistory"]
