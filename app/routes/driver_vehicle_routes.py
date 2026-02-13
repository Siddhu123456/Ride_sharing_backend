"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_vehicle_routes``. The real implementation now lives in
``app.routes.driver.vehicle``.
"""

from app.routes.driver.vehicle import router as router
