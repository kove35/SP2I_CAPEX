from __future__ import annotations

from pydantic import BaseModel, Field


ROLES = {"ADMIN", "MANAGER", "ANALYST", "VIEWER"}


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(default="")
    role: str = Field(default="ADMIN")


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
