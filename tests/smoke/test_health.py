import pytest
from src.api.booking_client import BookingClient

BASE_URL = "https://restful-booker.herokuapp.com"


@pytest.mark.smoke
class TestHealthCheck:
    def test_ping_returns_201(self):
        """API is alive and responding."""
        client = BookingClient(BASE_URL)
        response = client.health_check()
        assert response.status_code == 201
