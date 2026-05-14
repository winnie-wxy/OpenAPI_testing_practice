"""List and filter bookings — simulates partner-level query operations.

In a real XCover context, partners need to list their policies with filters
(by customer name, date range). At scale, this endpoint handles millions
of records — correct filtering and response shape are critical.
"""

import pytest
from src.utils.data_factory import build_booking_payload


@pytest.mark.regression
class TestListBookings:
    """GET /booking — returns list of booking IDs."""

    def test_list_bookings_returns_list(self, client):
        """Baseline: endpoint returns a non-empty list of booking objects."""
        response = client.get_bookings()
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) > 0

    def test_list_bookings_contains_booking_ids(self, client):
        """Each item in the list should have a bookingid field."""
        response = client.get_bookings()
        body = response.json()
        for item in body[:5]:  # check first 5 to avoid slow iteration
            assert "bookingid" in item
            assert isinstance(item["bookingid"], int)

    def test_created_booking_appears_in_list(self, created_booking, client):
        """A newly created booking should be queryable in the list."""
        booking_id, _ = created_booking
        response = client.get_bookings()
        all_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in all_ids, (
            f"Booking {booking_id} not found in list of {len(all_ids)} bookings"
        )


@pytest.mark.regression
class TestFilterBookingsByName:
    """GET /booking?firstname=X&lastname=Y — partner filtering by customer."""

    def test_filter_by_firstname(self, client):
        """Create a booking with known name, filter should return it."""
        unique_name = "FilterTestAlpha"
        payload = build_booking_payload(firstname=unique_name)
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        response = client.get_bookings(firstname=unique_name)
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids, (
            f"Booking {booking_id} with firstname='{unique_name}' "
            f"not found in filtered results"
        )

    def test_filter_by_lastname(self, client):
        unique_name = "FilterTestBeta"
        payload = build_booking_payload(lastname=unique_name)
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        response = client.get_bookings(lastname=unique_name)
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids, (
            f"Booking {booking_id} with lastname='{unique_name}' "
            f"not found in filtered results"
        )

    def test_filter_by_firstname_and_lastname(self, client):
        """Combined filter should narrow results."""
        payload = build_booking_payload(firstname="ComboFirst", lastname="ComboLast")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        response = client.get_bookings(firstname="ComboFirst", lastname="ComboLast")
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids

    def test_filter_nonexistent_name_returns_empty(self, client):
        """Filter with a name that doesn't exist should return empty list."""
        response = client.get_bookings(firstname="ZzNonExistentName99")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 0, (
            f"Expected empty list for non-existent name, got {len(body)} results"
        )


@pytest.mark.regression
class TestFilterBookingsByDate:
    """GET /booking?checkin=X&checkout=Y — date range filtering.

    In insurance context: "show me all policies bound between date X and Y."

    NOTE: Restful Booker date filter uses strict inequality for checkin
    (returns bookings with checkin > given date, not >=). This is a
    documented API quirk — a well-designed API should use >= for checkin
    and <= for checkout.
    """

    def test_filter_by_checkin_date(self, client):
        """checkin filter returns bookings with checkin AFTER the given date."""
        payload = build_booking_payload(checkin="2027-01-15", checkout="2027-01-20")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        # API quirk: checkin filter uses > not >= so we filter by day before
        response = client.get_bookings(checkin="2027-01-14")
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids

    def test_filter_by_checkout_date(self, client):
        payload = build_booking_payload(checkin="2027-02-01", checkout="2027-02-10")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        response = client.get_bookings(checkout="2027-02-10")
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids

    def test_filter_by_date_range(self, client):
        """Combined checkin + checkout filter — use day-before for checkin."""
        payload = build_booking_payload(checkin="2027-03-01", checkout="2027-03-15")
        create_resp = client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        # checkin uses >, checkout uses <= — so offset checkin by one day
        response = client.get_bookings(checkin="2027-02-28", checkout="2027-03-15")
        assert response.status_code == 200
        matching_ids = [item["bookingid"] for item in response.json()]
        assert booking_id in matching_ids
