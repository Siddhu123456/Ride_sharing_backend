"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_offer_routes``. The real implementation now lives in
``app.routes.driver.offers``.
"""

from app.routes.driver.offers import router as router


