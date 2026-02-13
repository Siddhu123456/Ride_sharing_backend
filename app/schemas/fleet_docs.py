"""Compatibility shim.

Implementation moved to `app.schemas.fleet_owner.fleet_docs`.
This module re-exports fleet-document schemas so existing imports continue to work.
"""

from app.schemas.fleet_owner.fleet_docs import (
    FleetDocumentUploadRequest,
    FleetDocumentResponse,
    FleetDocumentStatusResponse,
)

__all__ = [
    "FleetDocumentUploadRequest",
    "FleetDocumentResponse",
    "FleetDocumentStatusResponse",
]
