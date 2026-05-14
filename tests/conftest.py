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
def auth_credentials(load_env):
    """Return (username, password) from environment."""
    return (
        os.getenv("AUTH_USERNAME", "admin"),
        os.getenv("AUTH_PASSWORD", "password123"),
    )


@pytest.fixture(scope="session")
def auth_token(base_url, auth_credentials):
    """Authenticate once for the entire test session — avoids repeated /auth calls."""
    username, password = auth_credentials
    client = BookingClient(base_url)
    response = client.create_token(username, password)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="session")
def client(base_url, auth_token, auth_credentials):
    """Authenticated client with self-healing token refresh.

    Passes credentials so the client can re-authenticate on 403.
    """
    username, password = auth_credentials
    return BookingClient(
        base_url, token=auth_token, username=username, password=password,
    )


@pytest.fixture(scope="session")
def unauth_client(base_url):
    """Client without auth token — for testing unauthorized access."""
    return BookingClient(base_url)


@pytest.fixture
def created_booking(client):
    """Create a booking and guarantee cleanup after the test.

    Yields (booking_id, payload) so tests can use both.
    Teardown deletes the booking regardless of test outcome.
    """
    from src.utils.data_factory import build_booking_payload

    payload = build_booking_payload()
    response = client.create_booking(payload)
    assert response.status_code == 200, f"Setup failed: {response.text}"
    booking_id = response.json()["bookingid"]

    yield booking_id, payload

    # Teardown: delete the booking (ignore 404 if test already deleted it)
    client.delete_booking(booking_id)
