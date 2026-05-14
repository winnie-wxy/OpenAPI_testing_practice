"""Tests verifying the client's self-healing behaviours.

Covers:
- Auto-retry with exponential backoff on 5xx / 429
- Token refresh on 403 for mutating operations
- Schema tolerance for unexpected response fields
- Stale data detection via precondition checks
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.booking_client import BookingClient
from src.models.booking import Booking, BookingDates, BookingResponse


@pytest.mark.nonfunctional
class TestAutoRetry:
    """Verify the client retries on transient server errors."""

    def test_retries_on_500_then_succeeds(self):
        """Client retries on 500 and returns the successful response."""
        client = BookingClient("http://fake", max_retries=2, backoff_base=0.01)
        mock_fail = MagicMock(status_code=500, text="Internal Server Error")
        mock_ok = MagicMock(status_code=200, json=lambda: {"status": "ok"})

        with patch.object(client.session, "request", side_effect=[mock_fail, mock_ok]):
            response = client.health_check()

        assert response.status_code == 200

    def test_retries_on_429_rate_limit(self):
        """Client backs off and retries on 429 Too Many Requests."""
        client = BookingClient("http://fake", max_retries=2, backoff_base=0.01)
        mock_429 = MagicMock(status_code=429)
        mock_ok = MagicMock(status_code=200, json=lambda: {})

        with patch.object(client.session, "request", side_effect=[mock_429, mock_ok]):
            response = client.health_check()

        assert response.status_code == 200

    def test_retries_on_502_503_504(self):
        """Client retries on all gateway error codes."""
        for status in (502, 503, 504):
            client = BookingClient("http://fake", max_retries=1, backoff_base=0.01)
            mock_err = MagicMock(status_code=status)
            mock_ok = MagicMock(status_code=200)

            with patch.object(
                client.session, "request", side_effect=[mock_err, mock_ok]
            ):
                response = client.health_check()

            assert response.status_code == 200, f"Failed to recover from {status}"

    def test_returns_last_response_after_max_retries(self):
        """When all retries are exhausted, return the last error response."""
        client = BookingClient("http://fake", max_retries=2, backoff_base=0.01)
        mock_500 = MagicMock(status_code=500)

        with patch.object(
            client.session, "request", side_effect=[mock_500, mock_500, mock_500]
        ):
            response = client.health_check()

        assert response.status_code == 500

    def test_no_retry_on_4xx(self):
        """Client does not retry on non-retryable client errors (400, 404)."""
        client = BookingClient("http://fake", max_retries=3, backoff_base=0.01)
        mock_404 = MagicMock(status_code=404)

        with patch.object(client.session, "request", return_value=mock_404) as mock_req:
            response = client.get_booking(999)

        assert response.status_code == 404
        assert mock_req.call_count == 1

    def test_exponential_backoff_timing(self):
        """Verify backoff waits increase exponentially."""
        client = BookingClient("http://fake", max_retries=2, backoff_base=0.05)
        mock_500 = MagicMock(status_code=500)

        with patch.object(
            client.session, "request", side_effect=[mock_500, mock_500, mock_500]
        ):
            start = time.monotonic()
            client.health_check()
            elapsed = time.monotonic() - start

        # backoff_base=0.05: wait 0.05 + 0.10 = 0.15s minimum
        assert elapsed >= 0.14

    def test_retries_on_connection_error(self):
        """Client retries on ConnectionError and succeeds on next attempt."""
        client = BookingClient("http://fake", max_retries=2, backoff_base=0.01)
        mock_ok = MagicMock(status_code=200)

        with patch.object(
            client.session,
            "request",
            side_effect=[requests.ConnectionError("reset"), mock_ok],
        ):
            response = client.health_check()

        assert response.status_code == 200

    def test_connection_error_raises_after_max_retries(self):
        """ConnectionError propagates when retries are exhausted."""
        client = BookingClient("http://fake", max_retries=1, backoff_base=0.01)

        with patch.object(
            client.session,
            "request",
            side_effect=requests.ConnectionError("refused"),
        ):
            with pytest.raises(requests.ConnectionError):
                client.health_check()


@pytest.mark.nonfunctional
class TestTokenRefresh:
    """Verify transparent token refresh on 403."""

    def test_refreshes_token_on_403_for_put(self):
        """PUT that gets 403 triggers re-auth and retries."""
        client = BookingClient(
            "http://fake",
            token="expired",
            username="admin",
            password="password123",
            max_retries=0,
            backoff_base=0.01,
        )
        mock_403 = MagicMock(status_code=403)
        mock_200 = MagicMock(status_code=200)
        mock_auth = MagicMock(status_code=200)
        mock_auth.json.return_value = {"token": "new-token"}

        with patch.object(
            client.session,
            "request",
            side_effect=[mock_403, mock_auth, mock_200],
        ):
            response = client.update_booking(1, {"firstname": "Test"})

        assert response.status_code == 200

    def test_refreshes_token_on_403_for_delete(self):
        """DELETE that gets 403 triggers re-auth and retries."""
        client = BookingClient(
            "http://fake",
            token="expired",
            username="admin",
            password="password123",
            max_retries=0,
            backoff_base=0.01,
        )
        mock_403 = MagicMock(status_code=403)
        mock_200 = MagicMock(status_code=201)
        mock_auth = MagicMock(status_code=200)
        mock_auth.json.return_value = {"token": "new-token"}

        with patch.object(
            client.session,
            "request",
            side_effect=[mock_403, mock_auth, mock_200],
        ):
            response = client.delete_booking(1)

        assert response.status_code == 201

    def test_no_refresh_on_403_for_get(self):
        """GET requests don't trigger token refresh on 403."""
        client = BookingClient(
            "http://fake",
            token="expired",
            username="admin",
            password="password123",
            max_retries=0,
            backoff_base=0.01,
        )
        mock_403 = MagicMock(status_code=403)

        with patch.object(
            client.session, "request", return_value=mock_403
        ) as mock_req:
            response = client.get_booking(1)

        assert response.status_code == 403
        assert mock_req.call_count == 1

    def test_no_refresh_without_credentials(self):
        """Token refresh is skipped when credentials are not provided."""
        client = BookingClient(
            "http://fake", token="expired", max_retries=0, backoff_base=0.01,
        )
        mock_403 = MagicMock(status_code=403)

        with patch.object(
            client.session, "request", return_value=mock_403
        ) as mock_req:
            response = client.update_booking(1, {"firstname": "Test"})

        assert response.status_code == 403
        assert mock_req.call_count == 1

    def test_refresh_only_attempted_once(self):
        """Token refresh is only attempted once per request to avoid loops."""
        client = BookingClient(
            "http://fake",
            token="expired",
            username="admin",
            password="password123",
            max_retries=0,
            backoff_base=0.01,
        )
        mock_403 = MagicMock(status_code=403)
        mock_auth = MagicMock(status_code=200)
        mock_auth.json.return_value = {"token": "still-bad"}

        with patch.object(
            client.session,
            "request",
            side_effect=[mock_403, mock_auth, mock_403],
        ):
            response = client.update_booking(1, {"firstname": "Test"})

        assert response.status_code == 403


@pytest.mark.nonfunctional
class TestSchemaTolerance:
    """Verify Pydantic models tolerate unexpected fields."""

    def test_booking_ignores_extra_fields(self):
        """Booking model accepts unknown fields without raising."""
        data = {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 100,
            "depositpaid": True,
            "bookingdates": {"checkin": "2025-01-01", "checkout": "2025-01-08"},
            "additionalneeds": "Lunch",
            "loyalty_tier": "gold",
            "internal_flag": True,
        }
        booking = Booking(**data)
        assert booking.firstname == "Jim"
        assert booking.loyalty_tier == "gold"

    def test_booking_response_ignores_extra_fields(self):
        """BookingResponse model accepts unknown top-level fields."""
        data = {
            "bookingid": 42,
            "booking": {
                "firstname": "Jim",
                "lastname": "Brown",
                "totalprice": 100,
                "depositpaid": True,
                "bookingdates": {"checkin": "2025-01-01", "checkout": "2025-01-08"},
            },
            "_links": {"self": "/booking/42"},
        }
        resp = BookingResponse(**data)
        assert resp.bookingid == 42

    def test_booking_dates_ignores_extra_fields(self):
        """BookingDates model accepts unknown fields."""
        data = {"checkin": "2025-01-01", "checkout": "2025-01-08", "timezone": "UTC"}
        dates = BookingDates(**data)
        assert dates.checkin == "2025-01-01"
        assert dates.timezone == "UTC"

    def test_missing_required_field_still_fails(self):
        """Schema tolerance doesn't suppress missing required fields."""
        with pytest.raises(Exception):
            Booking(
                firstname="Jim",
                # lastname missing
                totalprice=100,
                depositpaid=True,
                bookingdates={"checkin": "2025-01-01", "checkout": "2025-01-08"},
            )


@pytest.mark.nonfunctional
class TestStaleDataDetection:
    """Verify precondition checks catch stale data before assertions."""

    def test_verify_booking_exists_before_update(self, client, created_booking):
        """Confirm the booking exists before attempting to update it."""
        booking_id, payload = created_booking

        get_response = client.get_booking(booking_id)
        assert get_response.status_code == 200, (
            f"Precondition failed: booking {booking_id} not found"
        )

        update_response = client.update_booking(booking_id, payload)
        assert update_response.status_code == 200

    def test_detect_stale_booking_after_delete(self, client, created_booking):
        """After deleting a booking, GET should confirm it's gone."""
        booking_id, _ = created_booking

        delete_response = client.delete_booking(booking_id)
        assert delete_response.status_code == 201

        get_response = client.get_booking(booking_id)
        assert get_response.status_code == 404, (
            f"Stale data: booking {booking_id} still returned after deletion"
        )
