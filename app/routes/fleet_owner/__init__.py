# Fleet owner domain package
# Implementation modules live in this package (fleet_owner.py, fleet_owner_driver.py, etc.)
# This file intentionally left minimal to avoid import side-effects.

__all__ = []
"""Fleet owner routes package.

This package contains the implementation modules for fleet-owner related
endpoints. The project keeps top-level route shims for backward
compatibility, while main imports are updated to reference these
implementation modules.
"""

__all__ = [
    "fleet_owner",
    "fleet_owner_driver",
    "fleet_owner_vehicle",
    "fleet_owner_vehicle_assignment",
]
