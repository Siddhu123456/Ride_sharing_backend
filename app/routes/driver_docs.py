"""Compatibility shim: re-export router from the new driver package.

This file is kept to preserve any direct imports that reference
``app.routes.driver_docs``. The real implementation now lives in
``app.routes.driver.docs``.
"""

from app.routes.driver.docs import router as router
