from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from src.infrastructure.database.models import UserRole


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.MEMBER


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


