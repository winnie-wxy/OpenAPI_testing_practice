"""Fixed versions of previously flaky tests.

Each fix addresses a specific anti-pattern:
1. Race condition → retry with polling
2. Shared state → isolated fixture per test
3. Non-deterministic timing → multi-sample P95 with tolerance
"""

import statistics
import time

import pytest
from src.utils.data_factory import build_booking_payload


def poll_booking(client, booking_id, expected_firstname, max_retries=3, delay=0.5):
    """Poll GET /booking until data is consistent or retries exhausted."""
    for attempt in range(max_retries):
        resp = client.get_booking(booking_id)
        if resp.status_code == 200:
            body = resp.json()
            if body.get("firstname") == expected_firstname:
                return body
        time.sleep(delay)
    pytest.fail(
        f"Booking {booking_id} not consistent after {max_retries} retries. "
        f"Expected firstname='{expected_firstname}'"
    )


@pytest.mark.regression
class TestFixedRaceCondition:
    """Fix: replace immediate read with retry/poll for eventual consistency."""

    def test_create_and_verify_with_polling(self, client):
        payload = build_booking_payload(
            firstname="RaceTest",
            lastname="Fixed",
            totalprice=999,
        )
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        # FIX: poll until consistent instead of assuming instant availability
        body = poll_booking(client, booking_id, expected_firstname="RaceTest")
        assert body["lastname"] == "Fixed"
        assert body["totalprice"] == 999


@pytest.mark.regression
class TestFixedIsolatedState:
    """Fix: replace shared module state with per-test fixture isolation."""

    def test_create_and_read_booking_isolated(self, client):
        """Each test creates its own data — no cross-test dependency."""
        payload = build_booking_payload(firstname="Isolated", lastname="State")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        resp = client.get_booking(booking_id)
        assert resp.status_code == 200
        assert resp.json()["firstname"] == "Isolated"

    def test_another_isolated_booking(self, client):
        """Independent test — can run in any order, in parallel."""
        payload = build_booking_payload(firstname="AlsoIsolated", lastname="NoSharing")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        resp = client.get_booking(booking_id)
        assert resp.status_code == 200
        assert resp.json()["firstname"] == "AlsoIsolated"


@pytest.mark.regression
class TestFixedTimingAssertion:
    """Fix: replace single-sample timing with statistical approach."""

    def test_response_time_p95_under_threshold(self, client):
        """Collect multiple samples and assert P95 — tolerant of outliers."""
        sample_size = 5
        threshold_ms = 2000
        times = []

        for _ in range(sample_size):
            payload = build_booking_payload()
            start = time.perf_counter()
            client.create_booking(payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        p95 = sorted(times)[int(len(times) * 0.95)]
        median = statistics.median(times)

        assert p95 < threshold_ms, (
            f"P95 response time {p95:.0f}ms exceeds {threshold_ms}ms "
            f"(median={median:.0f}ms, samples={[f'{t:.0f}' for t in times]})"
        )
