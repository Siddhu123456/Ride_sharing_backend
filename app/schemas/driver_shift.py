"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_shift import DriverShiftResponse``.
"""

from app.schemas.driver.driver_shift import StartDriverShiftRequest, EndDriverShiftRequest, DriverShiftResponse  # noqa: F401

__all__ = ["StartDriverShiftRequest", "EndDriverShiftRequest", "DriverShiftResponse"]

