"""Compatibility shim: re-export driver models from the driver package.

This preserves imports like ``from app.models.driver_profile import DriverProfile``.
The real definition now lives in ``app.models.driver.driver_profile``.
"""

from app.models.driver.driver_profile import DriverProfile  # noqa: F401

__all__ = ["DriverProfile"]
