"""Compatibility shim: re-export driver models from the driver package.

Preserves imports like ``from app.models.driver_document import DriverDocument``.
"""

from app.models.driver.driver_document import DriverDocument  # noqa: F401

__all__ = ["DriverDocument"]
