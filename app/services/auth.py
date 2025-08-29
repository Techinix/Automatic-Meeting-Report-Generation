"""
Authentication service.
"""

from datetime import datetime
from typing import Optional, Tuple, cast

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.schemas.token import TokenPayload


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate a user by username and password."""
    result = await db.execute(select(User).filter(User.username == username))
    user = cast(Optional[User], result.scalar_one_or_none())
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_tokens_for_user(user: User) -> Tuple[str, str]:
    """Create access and refresh tokens for a user."""
    access_token = create_access_token(user.username, str(user.id))
    refresh_token = create_refresh_token(user.username, str(user.id))
    return access_token, refresh_token


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> Optional[str]:
    """Create a new access token from a refresh token."""
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.exp and datetime.fromtimestamp(token_data.exp) < datetime.now():
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).filter(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    return create_access_token(user.username, str(user.id))
