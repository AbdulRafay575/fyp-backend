from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None

class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True