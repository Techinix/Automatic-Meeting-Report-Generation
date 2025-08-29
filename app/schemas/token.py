"""
Token schemas for authentication.
"""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""

    sub: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[int] = None


class RefreshToken(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str
