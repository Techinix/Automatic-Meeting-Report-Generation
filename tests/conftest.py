from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.base import Base

# Import all models here for autogenerate support
from app.db.session import AsyncSession, DatabaseSessionManager, get_db

# DONT REMOVE
from app.models.user import APIToken, User
from main import app

TEST_DATABASE_URL = settings.TEST_DATABASE_URL
test_db = DatabaseSessionManager(TEST_DATABASE_URL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_db() -> AsyncGenerator[None, None]:
    async with test_db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_db._engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_db.session() as session:
        yield session


# Inject override into app
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with test_db.session() as session:
        yield session
