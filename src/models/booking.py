from pydantic import BaseModel


class BookingDates(BaseModel):
    checkin: str
    checkout: str


class Booking(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None


class BookingResponse(BaseModel):
    bookingid: int
    booking: Booking
