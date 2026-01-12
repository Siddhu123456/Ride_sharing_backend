from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    password: str


class RegisterResponse(BaseModel):
    user_id: int
    message: str