"""Compatibility shim.

Implementation moved to `app.models.fleet_owner.commission_settlement`.
This module re-exports the `CommissionSettlement` model so existing imports continue to work.
"""

from app.models.fleet_owner.commission_settlement import CommissionSettlement

__all__ = ["CommissionSettlement"]
