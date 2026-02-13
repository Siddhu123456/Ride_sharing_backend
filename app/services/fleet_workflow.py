"""Compatibility shim.

Implementation moved to `app.services.fleet_owner.fleet_workflow`.
This module re-exports fleet workflow helpers so existing imports continue to work.
"""

from app.services.fleet_owner.fleet_workflow import (
    REQUIRED_DOC_TYPES,
    get_fleet_uploaded_docs,
    compute_doc_status,
    auto_approve_fleet_if_ready,
)

__all__ = [
    "REQUIRED_DOC_TYPES",
    "get_fleet_uploaded_docs",
    "compute_doc_status",
    "auto_approve_fleet_if_ready",
]
