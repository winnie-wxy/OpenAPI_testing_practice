from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from src.utils.data_factory import build_booking_payload

CONCURRENT_USERS = 10


@pytest.mark.nonfunctional
class TestConcurrentRequests:
    """Verify the API handles concurrent requests without errors.

    Simulates multiple users creating bookings simultaneously.
    Asserts no 5xx server errors under concurrent load.
    """

    def test_concurrent_booking_creation(self, client):
        """Create multiple bookings in parallel — no 5xx errors expected."""

        def create_booking():
            payload = build_booking_payload()
            response = client.create_booking(payload)
            return response.status_code, response.text

        results = []
        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            futures = [executor.submit(create_booking) for _ in range(CONCURRENT_USERS)]
            for future in as_completed(futures):
                status_code, body = future.result()
                results.append(status_code)

        server_errors = [code for code in results if code >= 500]
        assert len(server_errors) == 0, (
            f"{len(server_errors)}/{len(results)} requests returned 5xx: {server_errors}"
        )

        successful = [code for code in results if code == 200]
        assert len(successful) == CONCURRENT_USERS, (
            f"Only {len(successful)}/{CONCURRENT_USERS} requests succeeded. "
            f"Status codes: {results}"
        )

    def test_concurrent_read_operations(self, client):
        """Concurrent GET requests should all succeed."""
        payload = build_booking_payload()
        booking_id = client.create_booking(payload).json()["bookingid"]

        def get_booking():
            response = client.get_booking(booking_id)
            return response.status_code

        results = []
        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            futures = [executor.submit(get_booking) for _ in range(CONCURRENT_USERS)]
            for future in as_completed(futures):
                results.append(future.result())

        assert all(code == 200 for code in results), (
            f"Not all concurrent reads succeeded: {results}"
        )
