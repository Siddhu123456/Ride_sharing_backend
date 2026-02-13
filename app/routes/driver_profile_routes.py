"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_profile_routes``. The real implementation now lives in
``app.routes.driver.profile``.
"""

from app.routes.driver.profile import router as router

