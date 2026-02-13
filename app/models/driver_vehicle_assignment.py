"""Compatibility shim: re-export driver models from the driver package.

Preserves imports like ``from app.models.driver_vehicle_assignment import DriverVehicleAssignment``.
"""

from app.models.driver.driver_vehicle_assignment import DriverVehicleAssignment  # noqa: F401

__all__ = ["DriverVehicleAssignment"]
