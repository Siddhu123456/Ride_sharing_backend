"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_shift_location``. The real implementation now lives in
``app.routes.driver.shifts``.
"""

from app.routes.driver.shifts import router as router

