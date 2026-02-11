from enum import Enum

class UserRoleEnum(str, Enum):
    RIDER = "RIDER"
    DRIVER = "DRIVER"
    FLEET_OWNER = "FLEET_OWNER"
    TENANT_ADMIN = "TENANT_ADMIN"


    
class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class TenantRoleEnum(str, Enum):
    RIDER = 'RIDER'
    DRIVER = 'DRIVER'
    FLEET_OWNER = 'FLEET_OWNER'
    DISPATCHER = 'DISPATCHER'
    TENANT_ADMIN = 'TENANT_ADMIN'
    PLATFORM_ADMIN = 'PLATFORM_ADMIN'
    SUPPORT_AGENT = 'SUPPORT_AGENT'


class ApprovalStatusEnum(str, Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class AccountStatusEnum(str, Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    SUSPENDED = 'SUSPENDED'
    CLOSED = 'CLOSED'


class VehicleStatusEnum(str, Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    BLOCKED = 'BLOCKED'


class TripStatusEnum(str, Enum):
    REQUESTED = 'REQUESTED'
    ASSIGNED = 'ASSIGNED'
    PICKED_UP = 'PICKED_UP'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'


class FleetDocumentTypeEnum(str, Enum):
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    BUSINESS_REGISTRATION = "BUSINESS_REGISTRATION"


class DriverDocumentTypeEnum(str, Enum):
    DRIVING_LICENSE = "DRIVING_LICENSE"
    AADHAAR = "AADHAAR"
    PAN = "PAN"


class DriverTypeEnum(str, Enum):
    BIKE = "BIKE"
    AUTO = "AUTO"
    CAB = "CAB"


class VehicleCategoryEnum(str, Enum):
    BIKE = "BIKE"
    AUTO = "AUTO"
    CAB = "CAB"
    AC_CAB = "AC_CAB"


class VehicleDocumentTypeEnum(str, Enum):
    INSURANCE = "INSURANCE"
    REGISTRATION = "REGISTRATION"


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DriverShiftStatusEnum(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ON_TRIP = "ON_TRIP"


class WalletOwnerEnum(str, Enum):
    TENANT = "TENANT"
    FLEET_OWNER = "FLEET_OWNER"


class WalletTxnReasonEnum(str, Enum):
    TRIP_EARNING = "TRIP_EARNING"
    COMMISSION_LOCKED = "COMMISSION_LOCKED"
    COMMISSION_SETTLED = "COMMISSION_SETTLED"


class WalletTxnDirectionEnum(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    
    
class SettlementStatusEnum(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"