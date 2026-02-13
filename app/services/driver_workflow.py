"""Compatibility shim: re-export driver services from the driver package.

Preserves imports like ``from app.services.driver_workflow import get_uploaded_driver_docs``.
The real implementation lives in ``app.services.driver.driver_workflow``.
"""

from app.services.driver.driver_workflow import *  # noqa: F401,F403

__all__ = [
    "get_uploaded_driver_docs",
    "compute_driver_doc_status",
    "auto_approve_driver_if_ready",
]
