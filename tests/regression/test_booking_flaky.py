"""Intentional flaky test examples — demonstrating common anti-patterns.

These tests are DELIBERATELY flaky to illustrate patterns that cause
CI instability. Each will be fixed in a subsequent commit.

Anti-patterns demonstrated:
1. Race condition: create then immediately read without verification
2. Shared state: depending on a specific booking ID across tests
3. Non-deterministic timing: asserting exact response times
"""

import time

import pytest
from src.api.booking_client import BookingClient
from src.utils.data_factory import build_booking_payload

# ANTI-PATTERN: Shared mutable state across tests
_shared_booking_id = None


@pytest.mark.regression
class TestFlakyRaceCondition:
    """Anti-pattern: assumes immediate consistency after write."""

    def test_create_and_immediately_verify_details(self, client):
        """FLAKY: creates booking and immediately checks all fields.

        On slow networks or under load, the GET may return stale data
        or the booking may not be queryable yet.
        """
        payload = build_booking_payload(
            firstname="RaceTest",
            lastname="Flaky",
            totalprice=999,
        )
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        # ANTI-PATTERN: No wait, no retry — assumes instant consistency
        get_resp = client.get_booking(booking_id)
        body = get_resp.json()

        assert body["firstname"] == "RaceTest"
        assert body["lastname"] == "Flaky"
        assert body["totalprice"] == 999


@pytest.mark.regression
class TestFlakySharedState:
    """Anti-pattern: tests share state via module-level variable."""

    def test_step1_create_booking(self, client):
        """Creates a booking and stores ID in module-level variable."""
        global _shared_booking_id
        payload = build_booking_payload(firstname="Shared", lastname="State")
        resp = client.create_booking(payload)
        _shared_booking_id = resp.json()["bookingid"]
        assert _shared_booking_id is not None

    def test_step2_read_shared_booking(self, client):
        """FLAKY: depends on test_step1 running first AND succeeding.

        If tests run in parallel or random order, _shared_booking_id is None.
        If step1 failed, this test fails with a confusing error.
        """
        assert _shared_booking_id is not None, "Depends on test_step1 — shared state!"
        resp = client.get_booking(_shared_booking_id)
        assert resp.status_code == 200
        assert resp.json()["firstname"] == "Shared"


@pytest.mark.regression
class TestFlakyTimingAssertion:
    """Anti-pattern: asserting exact response time from a single request."""

    def test_response_time_under_threshold(self, client):
        """FLAKY: single-sample timing assertion without tolerance.

        Network jitter, server load, or CI runner contention can
        easily push a single request over the threshold.
        """
        payload = build_booking_payload()

        start = time.perf_counter()
        client.create_booking(payload)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # ANTI-PATTERN: hard threshold on single sample — no P95, no tolerance
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.0f}ms — too slow!"
