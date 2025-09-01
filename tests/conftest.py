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

import pytest
import subprocess
import httpx
import logging
from tenacity import retry, stop_after_delay, wait_fixed

# --- Configuration ---
# Base URL for the service running in Docker.
SERVICE_URL = "http://localhost:8000"
DOCKER_COMPOSE_FILE = "docker-compose.dev.yml"

logger = logging.getLogger("TestSetup")

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

@retry(stop=stop_after_delay(120), wait=wait_fixed(2))
def wait_for_service():
    """Polls the service's health check endpoint until it's responsive."""
    try:
        # Use a simple health check endpoint if you have one, otherwise the root is fine.
        # A dedicated /health endpoint is best practice.
        with httpx.Client() as client:
            response = client.get(f"{SERVICE_URL}/health") # Change to your health endpoint if you have one
            response.raise_for_status()  # Raise an exception for 4xx/5xx status codes
        logger.info("Service is up and running.")
    except (httpx.ConnectError, httpx.HTTPStatusError) as e:
        logger.info(f"Service not yet available ({e}). Retrying...")
        raise  # Re-raise the exception to trigger tenacity's retry mechanism

@pytest.fixture(scope="session")
def docker_services(request):
    """
    A session-scoped fixture to manage the lifecycle of Docker Compose services.
    """
    logger.info("Starting Docker services...")
    try:
        # The --build flag ensures we're testing the latest code.
        # The -d flag runs containers in the background.
        subprocess.run(
            ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "--build", "-d"],
            check=True,
            capture_output=True, # Hides docker-compose output unless there's an error
        )
        logger.info("Docker services started.")
    except subprocess.CalledProcessError as e:
        # If docker-compose fails, print the error and fail the tests.
        logger.error(f"Failed to start Docker services. Stderr: {e.stderr.decode()}")
        pytest.fail(f"Could not start Docker services: {e.stderr.decode()}", pytrace=False)

    # Define a teardown function using pytest's 'addfinalizer'.
    # This ensures services are torn down even if tests fail.
    def teardown():
        logger.info("Stopping Docker services...")
        subprocess.run(
            ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down"],
            check=True,
        )
        logger.info("Docker services stopped.")

    request.addfinalizer(teardown)

    # Wait for the service to become available before running tests.
    wait_for_service()
    
    # Return a value or simply yield to pass control
    yield

