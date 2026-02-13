"""Compatibility shim.

Implementation moved to `app.schemas.fleet_owner.fleet_settlement`.
This module re-exports fleet settlement schemas so existing imports continue to work.
"""

from app.schemas.fleet_owner.fleet_settlement import (
    FleetSettlementTripItem,
    FleetSettlementResponse,
    FleetSettlementPayResponse,
    SettlementTripItem,
    SettlementTransactionItem,
    FleetSettlementHistoryItem,
)

__all__ = [
    "FleetSettlementTripItem",
    "FleetSettlementResponse",
    "FleetSettlementPayResponse",
    "SettlementTripItem",
    "SettlementTransactionItem",
    "FleetSettlementHistoryItem",
]



