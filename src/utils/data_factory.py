import random
import string
from datetime import datetime, timedelta


def random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def build_booking_payload(
    firstname: str | None = None,
    lastname: str | None = None,
    totalprice: int | None = None,
    depositpaid: bool | None = None,
    checkin: str | None = None,
    checkout: str | None = None,
    additionalneeds: str | None = None,
) -> dict:
    today = datetime.now()
    return {
        "firstname": firstname or random_string(),
        "lastname": lastname or random_string(),
        "totalprice": totalprice if totalprice is not None else random.randint(50, 500),
        "depositpaid": depositpaid if depositpaid is not None else True,
        "bookingdates": {
            "checkin": checkin or today.strftime("%Y-%m-%d"),
            "checkout": checkout or (today + timedelta(days=7)).strftime("%Y-%m-%d"),
        },
        "additionalneeds": additionalneeds or "Breakfast",
    }
