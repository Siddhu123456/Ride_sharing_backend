from pydantic import BaseModel, EmailStr
from enum import Enum



class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class RegisterRequest(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    gender: GenderEnum
    country_code: str
    password: str


class RegisterResponse(BaseModel):
    user_id: int
    message: str