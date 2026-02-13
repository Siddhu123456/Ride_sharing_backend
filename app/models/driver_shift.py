"""Compatibility shim: re-export driver models from the driver package.

Preserves imports like ``from app.models.driver_shift import DriverShift``.
"""

from app.models.driver.driver_shift import DriverShift  # noqa: F401

__all__ = ["DriverShift"]
