from pydantic import BaseModel, EmailStr
from app.schemas.enums import GenderEnum
from typing import List

from app.schemas.enums import UserRoleEnum



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: int
    roles: List[UserRoleEnum]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class SelectRoleRequest(BaseModel):
    user_id: int
    role: UserRoleEnum