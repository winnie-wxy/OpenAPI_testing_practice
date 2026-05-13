import requests


class BookingClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        if token:
            self.session.cookies.set("token", token)

    def health_check(self) -> requests.Response:
        return self.session.get(f"{self.base_url}/ping")

    def create_token(self, username: str, password: str) -> requests.Response:
        return self.session.post(
            f"{self.base_url}/auth",
            json={"username": username, "password": password},
        )

    def get_bookings(self, **params) -> requests.Response:
        return self.session.get(f"{self.base_url}/booking", params=params)

    def get_booking(self, booking_id: int) -> requests.Response:
        return self.session.get(f"{self.base_url}/booking/{booking_id}")

    def create_booking(self, payload: dict) -> requests.Response:
        return self.session.post(f"{self.base_url}/booking", json=payload)

    def update_booking(self, booking_id: int, payload: dict) -> requests.Response:
        return self.session.put(f"{self.base_url}/booking/{booking_id}", json=payload)

    def partial_update_booking(self, booking_id: int, payload: dict) -> requests.Response:
        return self.session.patch(f"{self.base_url}/booking/{booking_id}", json=payload)

    def delete_booking(self, booking_id: int) -> requests.Response:
        return self.session.delete(f"{self.base_url}/booking/{booking_id}")
