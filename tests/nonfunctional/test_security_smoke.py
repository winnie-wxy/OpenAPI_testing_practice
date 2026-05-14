import pytest
from src.utils.data_factory import build_booking_payload


@pytest.mark.nonfunctional
class TestSecuritySmoke:
    """Basic security smoke tests — not a penetration test, but catches obvious gaps.

    Validates the API doesn't blindly accept malicious input patterns.
    """

    def test_auth_bypass_with_empty_token(self, base_url):
        """Verify API rejects requests with empty/invalid auth tokens."""
        from src.api.booking_client import BookingClient

        client = BookingClient(base_url, token="")
        payload = build_booking_payload()
        booking_id = client.create_booking(payload).json()["bookingid"]

        # Should not be able to update with empty token
        response = client.update_booking(booking_id, payload)
        assert response.status_code in (401, 403), (
            f"Expected 401/403 for empty token, got {response.status_code}"
        )

    def test_sql_injection_in_booking_fields(self, client):
        """Verify SQL injection payloads don't cause server errors."""
        sql_payloads = [
            "'; DROP TABLE bookings; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
        ]
        for sql_payload in sql_payloads:
            payload = build_booking_payload(
                firstname=sql_payload,
                lastname=sql_payload,
            )
            response = client.create_booking(payload)
            assert response.status_code != 500, (
                f"Server error with SQL injection payload: {sql_payload}"
            )

    def test_xss_in_booking_fields(self, client):
        """Verify XSS payloads are handled without server error."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(document.cookie)",
        ]
        for xss_payload in xss_payloads:
            payload = build_booking_payload(
                firstname=xss_payload,
                additionalneeds=xss_payload,
            )
            response = client.create_booking(payload)
            assert response.status_code != 500, (
                f"Server error with XSS payload: {xss_payload}"
            )

    def test_oversized_payload(self, client):
        """Verify API handles abnormally large payloads without crashing."""
        large_string = "A" * 100_000
        payload = build_booking_payload(
            firstname=large_string,
            lastname=large_string,
        )
        response = client.create_booking(payload)
        # Should either accept (lenient) or reject (413/400) — not crash (500)
        assert response.status_code != 500, (
            "Server error with oversized payload — missing input size validation"
        )

    def test_special_characters_in_fields(self, client):
        """Verify special characters don't break the API."""
        special_chars = [
            "O'Brien",
            'He said "hello"',
            "Back\\slash",
            "New\nline",
            "Tab\there",
            "Null\x00char",
        ]
        for name in special_chars:
            payload = build_booking_payload(firstname=name)
            response = client.create_booking(payload)
            assert response.status_code != 500, (
                f"Server error with special character: {repr(name)}"
            )
