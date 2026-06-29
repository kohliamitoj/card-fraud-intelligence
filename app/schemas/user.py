from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Literal


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    role: Literal["analyst", "senior_analyst", "manager"] = "analyst"


class UserInDB(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
