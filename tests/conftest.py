import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.api.booking_client import BookingClient

ENV_FILES = {
    "dev": ".env",
    "staging": ".env.staging",
    "prod": ".env.prod",
}


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        choices=list(ENV_FILES.keys()),
        help="Target environment: dev (default), staging, prod",
    )


@pytest.fixture(scope="session", autouse=True)
def load_env(request):
    """Load environment variables from the appropriate .env file."""
    env_name = request.config.getoption("--env")
    env_file = Path(__file__).parent.parent / ENV_FILES.get(env_name, ".env")
    load_dotenv(env_file, override=True)


@pytest.fixture(scope="session")
def base_url(load_env):
    return os.getenv("BASE_URL", "https://restful-booker.herokuapp.com")


@pytest.fixture(scope="session")
def auth_token(base_url):
    """Authenticate once for the entire test session — avoids repeated /auth calls."""
    username = os.getenv("AUTH_USERNAME", "admin")
    password = os.getenv("AUTH_PASSWORD", "password123")
    client = BookingClient(base_url)
    response = client.create_token(username, password)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="session")
def client(base_url, auth_token):
    """Authenticated client shared across all tests in the session."""
    return BookingClient(base_url, token=auth_token)


@pytest.fixture(scope="session")
def unauth_client(base_url):
    """Client without auth token — for testing unauthorized access."""
    return BookingClient(base_url)
