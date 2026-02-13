"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_dashboard_routes``. The real implementation now lives in
``app.routes.driver.dashboard``.
"""

from app.routes.driver.dashboard import router as router


