"""
User schemas for request and response validation.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    username: str


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for user update."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserOut(UserBase):
    """Schema for user response."""

    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)
