"""Driver domain models package.

This package groups driver-related ORM models. Original top-level
modules in `app.models` keep compatibility shims that re-export symbols
from here.
"""

from .driver_profile import DriverProfile
from .driver_location import DriverLocation
from .driver_location_history import DriverLocationHistory
from .driver_shift import DriverShift
from .driver_vehicle_assignment import DriverVehicleAssignment
from .driver_document import DriverDocument

__all__ = [
    "DriverProfile",
    "DriverLocation",
    "DriverLocationHistory",
    "DriverShift",
    "DriverVehicleAssignment",
    "DriverDocument",
]
