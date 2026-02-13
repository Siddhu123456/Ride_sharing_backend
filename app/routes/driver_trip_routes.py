"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_trip_routes``. The real implementation now lives in
``app.routes.driver.trips``.
"""

from app.routes.driver.trips import router as router