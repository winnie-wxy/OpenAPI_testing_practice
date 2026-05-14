import logging
import time

import requests

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 0.5


class BookingClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        if token:
            self.session.cookies.set("token", token)

    def _refresh_token(self) -> bool:
        """Re-authenticate and update the session cookie.

        Returns True if refresh succeeded, False if credentials are unavailable
        or auth fails.
        """
        if not self.username or not self.password:
            return False
        try:
            response = self.session.request(
                "POST",
                f"{self.base_url}/auth",
                json={"username": self.username, "password": self.password},
            )
            if response.status_code == 200:
                token = response.json().get("token")
                if token:
                    self.session.cookies.set("token", token)
                    logger.info("Token refreshed successfully")
                    return True
        except requests.RequestException:
            logger.warning("Token refresh failed due to connection error")
        return False

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute an HTTP request with retry and token refresh.

        Retries on 5xx/429 with exponential backoff.
        On 403 for mutating operations, attempts token refresh once
        (does not consume the retry budget).
        """
        last_response = None
        token_refreshed = False
        attempt = 0
        max_attempts = self.max_retries + 1

        while attempt < max_attempts:
            try:
                response = self.session.request(method, url, **kwargs)
            except requests.ConnectionError as e:
                if attempt < self.max_retries:
                    wait = self.backoff_base * (2**attempt)
                    logger.warning(
                        "Connection error on attempt %d/%d, retrying in %.1fs: %s",
                        attempt + 1, max_attempts, wait, e,
                    )
                    time.sleep(wait)
                    attempt += 1
                    continue
                raise

            last_response = response

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < self.max_retries:
                    wait = self.backoff_base * (2**attempt)
                    logger.warning(
                        "%s %s returned %d, retrying in %.1fs (attempt %d/%d)",
                        method, url, response.status_code, wait,
                        attempt + 1, max_attempts,
                    )
                    time.sleep(wait)
                    attempt += 1
                    continue
                return response

            if (
                response.status_code == 403
                and method.upper() in ("PUT", "PATCH", "DELETE")
                and not token_refreshed
            ):
                logger.info("Got 403 on %s %s, attempting token refresh", method, url)
                if self._refresh_token():
                    token_refreshed = True
                    # Don't increment attempt — token refresh is free
                    continue

            return response

        return last_response

    def health_check(self) -> requests.Response:
        return self._request("GET", f"{self.base_url}/ping")

    def create_token(self, username: str, password: str) -> requests.Response:
        return self._request(
            "POST",
            f"{self.base_url}/auth",
            json={"username": username, "password": password},
        )

    def get_bookings(self, **params) -> requests.Response:
        return self._request("GET", f"{self.base_url}/booking", params=params)

    def get_booking(self, booking_id: int) -> requests.Response:
        return self._request("GET", f"{self.base_url}/booking/{booking_id}")

    def create_booking(self, payload: dict) -> requests.Response:
        return self._request("POST", f"{self.base_url}/booking", json=payload)

    def update_booking(self, booking_id: int, payload: dict) -> requests.Response:
        return self._request(
            "PUT", f"{self.base_url}/booking/{booking_id}", json=payload
        )

    def partial_update_booking(
        self, booking_id: int, payload: dict
    ) -> requests.Response:
        return self._request(
            "PATCH", f"{self.base_url}/booking/{booking_id}", json=payload
        )

    def delete_booking(self, booking_id: int) -> requests.Response:
        return self._request(
            "DELETE", f"{self.base_url}/booking/{booking_id}"
        )
