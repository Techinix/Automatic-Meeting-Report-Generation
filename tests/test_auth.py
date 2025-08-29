import secrets
from typing import cast, Optional, Any

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import APIToken, User


@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    result = await session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one_or_none()
    if user:
        return cast(User, user)

    user = User(username="testuser", hashed_password=get_password_hash("secret123"))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return cast(User, user)


@pytest_asyncio.fixture
async def jwt_token(test_user: User) -> str:
    token = create_access_token("test", test_user.id)
    return f"Bearer {token}"


@pytest_asyncio.fixture
async def api_token(test_user: User, session: AsyncSession) -> str:
    token_str = secrets.token_hex(32)
    token = APIToken(token=token_str, user_id=test_user.id)
    session.add(token)
    await session.commit()
    return token_str


@pytest.mark.asyncio
async def test_signup_success(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "auth/signup", json={"username": "newuser", "password": "pass1234"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"


@pytest.mark.asyncio
async def test_signup_duplicate_username(
    async_client: AsyncClient, test_user: User
) -> None:
    response = await async_client.post(
        "auth/signup", json={"username": "testuser", "password": "secret123"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "User with similar username or email already exists"
    )


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User) -> None:
    response = await async_client.post(
        "auth/login", json={"username": "testuser", "password": "secret123"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "auth/login", json={"username": "fakeuser", "password": "wrongpass"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_token_refresh_success(
    async_client: AsyncClient, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Create mock token and patch function
    refresh_token_str = "valid-refresh-token"

    async def mock_refresh_token(token: str, db: Any) -> Optional[str]:
        return "new-access-token" if token == refresh_token_str else None

    monkeypatch.setattr("app.api.auth.refresh_access_token", mock_refresh_token)

    response = await async_client.post(
        "auth/token/refresh", json={"refresh_token": refresh_token_str}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "new-access-token"
    assert data["refresh_token"] == refresh_token_str
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_token_refresh_invalid(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_refresh_token(token: Any, db: Any) -> None:
        return None

    monkeypatch.setattr("app.api.auth.refresh_access_token", mock_refresh_token)

    response = await async_client.post(
        "auth/token/refresh", json={"refresh_token": "invalid-token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_read_users_me(async_client: AsyncClient, jwt_token: str) -> None:
    response = await async_client.get("auth/me", headers={"Authorization": jwt_token})
    assert response.status_code == 200
    data = response.json()
    assert "username" in data


@pytest.mark.asyncio
async def test_read_users_api_me(async_client: AsyncClient, api_token: str) -> None:
    response = await async_client.get("auth/api-me", headers={"X-API-Token": api_token})
    assert response.status_code == 200
    data = response.json()
    assert "username" in data


@pytest.mark.asyncio
async def test_me_unauthorized(async_client: AsyncClient) -> None:
    response = await async_client.get("auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_me_unauthorized(async_client: AsyncClient) -> None:
    response = await async_client.get("auth/api-me")
    assert response.status_code == 401
