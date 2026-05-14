import pytest
import requests
from src.api.booking_client import BookingClient


@pytest.mark.nonfunctional
class TestResilience:
    """Verify the client handles infrastructure-level failures gracefully."""

    def test_connection_to_invalid_host_raises(self):
        """Client should raise a clear error for unreachable hosts."""
        client = BookingClient("https://nonexistent.invalid.host.example.com")
        with pytest.raises(requests.exceptions.ConnectionError):
            client.health_check()

    def test_request_timeout_handling(self, base_url):
        """Verify timeout parameter is respected by the transport layer."""
        client = BookingClient(base_url)
        with pytest.raises((requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError)):
            # Pass timeout directly to the request — 0.001s is too short for any response
            client.session.get(f"{base_url}/ping", timeout=0.001)

    def test_malformed_url_handling(self):
        """Client should handle malformed base URL gracefully."""
        client = BookingClient("not-a-valid-url")
        with pytest.raises(requests.exceptions.RequestException):
            client.health_check()
