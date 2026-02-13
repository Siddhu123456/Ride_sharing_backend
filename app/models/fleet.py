"""Compatibility shim.

Implementation moved to `app.models.fleet_owner.fleet`.
This module re-exports the `Fleet` model so existing imports continue to work.
"""

from app.models.fleet_owner.fleet import Fleet

__all__ = ["Fleet"]
