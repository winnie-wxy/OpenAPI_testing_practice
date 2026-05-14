import statistics
import time

import pytest
from src.utils.data_factory import build_booking_payload

RESPONSE_TIME_THRESHOLD_MS = 2000
SAMPLE_SIZE = 5


@pytest.mark.nonfunctional
class TestResponseTime:
    """Verify API response times stay within acceptable thresholds.

    Uses P95 approach: collect multiple samples, assert the 95th percentile
    is under threshold. This avoids false failures from single slow requests.
    """

    @staticmethod
    def _measure_ms(func, *args, **kwargs):
        start = time.perf_counter()
        response = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return response, elapsed_ms

    def test_health_check_response_time(self, unauth_client):
        times = []
        for _ in range(SAMPLE_SIZE):
            _, elapsed = self._measure_ms(unauth_client.health_check)
            times.append(elapsed)

        p95 = sorted(times)[int(len(times) * 0.95)]
        assert p95 < RESPONSE_TIME_THRESHOLD_MS, (
            f"Health check P95 response time {p95:.0f}ms exceeds {RESPONSE_TIME_THRESHOLD_MS}ms"
        )

    def test_get_booking_response_time(self, client):
        payload = build_booking_payload()
        booking_id = client.create_booking(payload).json()["bookingid"]

        times = []
        for _ in range(SAMPLE_SIZE):
            _, elapsed = self._measure_ms(client.get_booking, booking_id)
            times.append(elapsed)

        p95 = sorted(times)[int(len(times) * 0.95)]
        assert p95 < RESPONSE_TIME_THRESHOLD_MS, (
            f"GET booking P95 response time {p95:.0f}ms exceeds {RESPONSE_TIME_THRESHOLD_MS}ms"
        )

    def test_create_booking_response_time(self, client):
        times = []
        for _ in range(SAMPLE_SIZE):
            payload = build_booking_payload()
            _, elapsed = self._measure_ms(client.create_booking, payload)
            times.append(elapsed)

        p95 = sorted(times)[int(len(times) * 0.95)]
        assert p95 < RESPONSE_TIME_THRESHOLD_MS, (
            f"POST booking P95 response time {p95:.0f}ms exceeds {RESPONSE_TIME_THRESHOLD_MS}ms"
        )

    def test_response_times_summary(self, client, unauth_client):
        """Collect and report response time stats across endpoints."""
        results = {}

        # Health check
        times = []
        for _ in range(SAMPLE_SIZE):
            _, elapsed = self._measure_ms(unauth_client.health_check)
            times.append(elapsed)
        results["GET /ping"] = times

        # Create booking
        times = []
        for _ in range(SAMPLE_SIZE):
            payload = build_booking_payload()
            _, elapsed = self._measure_ms(client.create_booking, payload)
            times.append(elapsed)
        results["POST /booking"] = times

        for endpoint, times in results.items():
            p50 = statistics.median(times)
            p95 = sorted(times)[int(len(times) * 0.95)]
            mean = statistics.mean(times)
            print(f"\n{endpoint}: mean={mean:.0f}ms, P50={p50:.0f}ms, P95={p95:.0f}ms")

        # All endpoints should be under threshold
        for endpoint, times in results.items():
            p95 = sorted(times)[int(len(times) * 0.95)]
            assert p95 < RESPONSE_TIME_THRESHOLD_MS, f"{endpoint} P95 too slow: {p95:.0f}ms"
