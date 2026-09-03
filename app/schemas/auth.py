from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str


class UserReadSchema(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerifyEmailSchema(BaseModel):
    user_id: int
    code: str = Field(..., min_length=6, max_length=6, description="6-значный OTP код")


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenInputSchema(BaseModel):
    refresh_token: str