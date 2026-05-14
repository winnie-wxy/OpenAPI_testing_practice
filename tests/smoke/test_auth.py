import pytest
from src.api.booking_client import BookingClient


@pytest.mark.smoke
class TestAuth:
    def test_valid_credentials_returns_token(self, base_url):
        client = BookingClient(base_url)
        response = client.create_token("admin", "password123")
        assert response.status_code == 200
        assert "token" in response.json()

    def test_invalid_credentials_rejected(self, base_url):
        client = BookingClient(base_url)
        response = client.create_token("wrong", "wrong")
        assert response.status_code == 200  # API returns 200 with reason, not 401
        body = response.json()
        assert body.get("reason") == "Bad credentials"
