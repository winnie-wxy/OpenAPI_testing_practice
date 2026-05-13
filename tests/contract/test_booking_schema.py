import pytest
from pydantic import ValidationError
from src.models.booking import Booking, BookingResponse
from src.utils.data_factory import build_booking_payload


@pytest.mark.contract
class TestBookingResponseSchema:
    """Validate API responses match the expected contract.

    If the API adds, removes, or renames a field — these tests catch it.
    Same concept as Pact consumer-driven contracts, but for response shape.
    """

    def test_create_booking_response_matches_schema(self, client):
        payload = build_booking_payload()
        response = client.create_booking(payload)
        body = response.json()

        # Pydantic will raise ValidationError if shape doesn't match
        validated = BookingResponse(**body)
        assert validated.bookingid > 0
        assert validated.booking.firstname == payload["firstname"]

    def test_get_booking_response_matches_schema(self, client):
        payload = build_booking_payload()
        booking_id = client.create_booking(payload).json()["bookingid"]

        response = client.get_booking(booking_id)
        body = response.json()

        validated = Booking(**body)
        assert validated.firstname == payload["firstname"]
        assert validated.bookingdates.checkin == payload["bookingdates"]["checkin"]

    def test_invalid_response_shape_detected(self):
        """Prove that Pydantic actually catches schema violations."""
        with pytest.raises(ValidationError):
            BookingResponse(**{"unexpected": "shape"})

        with pytest.raises(ValidationError):
            Booking(**{"firstname": "only"})  # missing required fields
