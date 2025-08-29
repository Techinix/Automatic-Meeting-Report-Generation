"""
Authentication routes.
"""

import secrets
from typing import Dict

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy import select

from app.api.deps import AuthUserDep, DBSessionDep, TokenUserDep
from app.core.security import get_password_hash
from app.models.user import APIToken, User
from app.schemas.token import RefreshToken, Token
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.auth import (
    authenticate_user,
    create_tokens_for_user,
    refresh_access_token,
)

router = APIRouter()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: DBSessionDep) -> User:
    """Register a new user."""
    # Check if username or email already exists
    result = await db.execute(select(User).filter(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with similar username or email already exists",
        )

    # Create new user
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: DBSessionDep,
) -> Dict:
    """Authenticate user and return tokens."""
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = await create_tokens_for_user(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token/refresh", response_model=Token)
async def refresh_token(token_data: RefreshToken, db: DBSessionDep) -> Dict:
    """Refresh access token."""
    new_access_token = await refresh_access_token(token_data.refresh_token, db)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": new_access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: AuthUserDep) -> User:
    """Get current user info."""
    return current_user


@router.get("/api-me", response_model=UserOut)
async def read_users_api_me(
    current_user: TokenUserDep,
    # Leave this for swagger display
    token: str = Header(None, alias="X-API-Token"),
) -> User:
    """Get current user info."""
    return current_user


@router.post("/api-token")
async def create_api_token(
    db: DBSessionDep,
    user: AuthUserDep,
) -> Dict:
    token_value = secrets.token_hex(32)
    db_token = APIToken(token=token_value, user_id=user.id)
    db.add(db_token)
    await db.commit()
    return {"api_token": token_value}
