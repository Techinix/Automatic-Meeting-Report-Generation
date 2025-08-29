"""
API dependencies.
"""

from datetime import datetime
from typing import Annotated, Optional, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.user import APIToken, User
from app.schemas.token import TokenPayload

DBSessionDep = Annotated[AsyncSession, Depends(get_db)]


# OAuth2 scheme for token authentication
oauth2_scheme = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_user(
    db: DBSessionDep,
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not token:
            raise credentials_exception
        token_seg = token.split(" ")
        if len(token_seg) != 2 or token_seg[0] != "Bearer":
            raise credentials_exception

        payload = jwt.decode(
            token_seg[1], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.exp and datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.id == token_data.user_id))
    user = cast(Optional[User], result.scalar_one_or_none())
    if user is None:
        raise credentials_exception
    return user


AuthUserDep = Annotated[User, Depends(get_current_user)]

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


async def get_current_user_token(
    db: DBSessionDep, api_token: str = Depends(api_key_header)
) -> User:
    if not api_token:
        raise HTTPException(status_code=401, detail="API token missing")

    result = await db.execute(
        select(APIToken)
        .options(selectinload(APIToken.user))
        .filter(APIToken.token == api_token)
    )
    token_record = cast(Optional[APIToken], result.scalar_one_or_none())
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return cast(User, token_record.user)


TokenUserDep = Annotated[User, Depends(get_current_user_token)]
