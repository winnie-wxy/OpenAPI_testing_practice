import pytest
from src.utils.data_factory import build_booking_payload


@pytest.mark.regression
class TestBookingLifecycle:
    """Full CRUD lifecycle — the most valuable test in the suite.

    Simulates: partner authenticates → binds policy → customer views →
    changes dates → cancels → policy is gone.
    """

    def test_full_crud_lifecycle(self, client):
        # CREATE
        payload = build_booking_payload(firstname="Lifecycle", lastname="Test")
        create_resp = client.create_booking(payload)
        assert create_resp.status_code == 200
        booking_id = create_resp.json()["bookingid"]

        # READ — verify data persisted correctly
        get_resp = client.get_booking(booking_id)
        assert get_resp.status_code == 200
        assert get_resp.json()["firstname"] == "Lifecycle"

        # UPDATE (PUT) — change dates, like a customer rebooking
        updated_payload = build_booking_payload(
            firstname="Lifecycle",
            lastname="Updated",
            checkin="2026-07-01",
            checkout="2026-07-10",
        )
        update_resp = client.update_booking(booking_id, updated_payload)
        assert update_resp.status_code == 200
        assert update_resp.json()["lastname"] == "Updated"
        assert update_resp.json()["bookingdates"]["checkin"] == "2026-07-01"

        # PARTIAL UPDATE (PATCH) — only change one field
        patch_resp = client.partial_update_booking(booking_id, {"firstname": "Patched"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["firstname"] == "Patched"
        assert patch_resp.json()["lastname"] == "Updated"  # unchanged

        # DELETE — cancel the booking
        delete_resp = client.delete_booking(booking_id)
        assert delete_resp.status_code == 201  # Restful Booker quirk

        # VERIFY DELETED — GET should return 404
        get_deleted = client.get_booking(booking_id)
        assert get_deleted.status_code == 404
