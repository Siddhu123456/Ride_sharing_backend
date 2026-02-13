"""Driver domain schemas package.

This package groups driver-related Pydantic schemas. Top-level schema
modules keep compatibility shims that re-export from here.
"""

from .driver_profile import DriverProfileResponse
from .driver_shift import (
    StartDriverShiftRequest,
    EndDriverShiftRequest,
    DriverShiftResponse,
)
from .driver_location import UpdateDriverLocationRequest, DriverLocationResponse
from .driver_trip import ActiveTripResponse, DriverTripItem, DriverTripListResponse
from .driver_offers import DriverOfferResponse, DriverOfferRespondRequest
from .driver_docs import DriverDocumentUploadRequest, DriverDocumentResponse, DriverDocumentStatusResponse
from .driver_dashboard import (
    DriverDashboardSummaryResponse,
    DriverDashboardTenant,
    DriverDashboardFleet,
    DriverDashboardTodayStats,
    DriverDashboardCurrentShift,
)
from .driver_vehicle import DriverVehicleAssignmentResponse

__all__ = [
    "DriverProfileResponse",
    "StartDriverShiftRequest",
    "EndDriverShiftRequest",
    "DriverShiftResponse",
    "UpdateDriverLocationRequest",
    "DriverLocationResponse",
    "ActiveTripResponse",
    "DriverTripItem",
    "DriverTripListResponse",
    "DriverOfferResponse",
    "DriverOfferRespondRequest",
    "DriverDocumentUploadRequest",
    "DriverDocumentResponse",
    "DriverDocumentStatusResponse",
    "DriverDashboardSummaryResponse",
    "DriverVehicleAssignmentResponse",
]
