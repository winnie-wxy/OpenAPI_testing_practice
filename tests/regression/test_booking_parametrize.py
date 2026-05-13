import pytest
from src.utils.data_factory import build_booking_payload


@pytest.mark.regression
class TestCreateBookingVariations:
    """Data-driven tests — one function, many scenarios."""

    @pytest.mark.parametrize(
        "firstname, lastname, totalprice",
        [
            ("Alice", "Smith", 100),
            ("Bob", "O'Brien", 0),
            ("María", "García", 999),
            ("Li", "W", 1),
        ],
        ids=["standard", "apostrophe_in_name", "unicode_name", "minimum_length_name"],
    )
    def test_create_booking_with_varied_data(self, client, firstname, lastname, totalprice):
        payload = build_booking_payload(
            firstname=firstname,
            lastname=lastname,
            totalprice=totalprice,
        )
        response = client.create_booking(payload)
        assert response.status_code == 200
        body = response.json()
        assert body["booking"]["firstname"] == firstname
        assert body["booking"]["lastname"] == lastname
        assert body["booking"]["totalprice"] == totalprice

    @pytest.mark.parametrize("depositpaid", [True, False], ids=["paid", "unpaid"])
    def test_create_booking_deposit_status(self, client, depositpaid):
        payload = build_booking_payload(depositpaid=depositpaid)
        response = client.create_booking(payload)
        assert response.status_code == 200
        assert response.json()["booking"]["depositpaid"] == depositpaid
