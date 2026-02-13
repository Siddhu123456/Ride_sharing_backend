"""Compatibility shim: re-export driver availability services from the driver package.

Preserves imports like ``from app.services.driver_availability_service import count_available_drivers_by_vehicle``.
The real implementation lives in ``app.services.driver.driver_availability_service``.
"""

from app.services.driver.driver_availability_service import *  # noqa: F401,F403

__all__ = ["count_available_drivers_by_vehicle"]
