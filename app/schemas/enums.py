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