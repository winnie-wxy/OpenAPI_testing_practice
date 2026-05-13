import pytest
from src.utils.data_factory import build_booking_payload


@pytest.mark.smoke
class TestCreateBooking:
    def test_create_booking_returns_id(self, client):
        payload = build_booking_payload()
        response = client.create_booking(payload)
        assert response.status_code == 200
        body = response.json()
        assert "bookingid" in body
        assert isinstance(body["bookingid"], int)

    def test_created_booking_matches_payload(self, client):
        payload = build_booking_payload(firstname="Winnie", lastname="Wei")
        response = client.create_booking(payload)
        body = response.json()
        booking = body["booking"]
        assert booking["firstname"] == "Winnie"
        assert booking["lastname"] == "Wei"
        assert booking["bookingdates"] == payload["bookingdates"]

    def test_get_booking_after_create(self, client):
        payload = build_booking_payload()
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        get_resp = client.get_booking(booking_id)
        assert get_resp.status_code == 200
        assert get_resp.json()["firstname"] == payload["firstname"]
