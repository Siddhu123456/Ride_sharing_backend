"""Compatibility shim: re-export driver schemas from the driver package.

Preserves imports like ``from app.schemas.driver_offers import DriverOfferResponse``.
"""

from app.schemas.driver.driver_offers import DriverOfferResponse, DriverOfferRespondRequest  # noqa: F401

__all__ = ["DriverOfferResponse", "DriverOfferRespondRequest"]
