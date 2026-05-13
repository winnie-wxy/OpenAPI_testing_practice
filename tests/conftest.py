import pytest
from src.api.booking_client import BookingClient

BASE_URL = "https://restful-booker.herokuapp.com"
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "password123"


@pytest.fixture(scope="session")
def auth_token():
    """Authenticate once for the entire test session — avoids repeated /auth calls."""
    client = BookingClient(BASE_URL)
    response = client.create_token(AUTH_USERNAME, AUTH_PASSWORD)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token = response.json()["token"]
    return token


@pytest.fixture(scope="session")
def client(auth_token):
    """Authenticated client shared across all tests in the session."""
    return BookingClient(BASE_URL, token=auth_token)


@pytest.fixture(scope="session")
def unauth_client():
    """Client without auth token — for testing unauthorized access."""
    return BookingClient(BASE_URL)
