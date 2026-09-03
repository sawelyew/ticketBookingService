from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserProfileSchema(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)