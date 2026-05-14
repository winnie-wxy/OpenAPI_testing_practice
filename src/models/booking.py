from pydantic import BaseModel, ConfigDict


class BookingDates(BaseModel):
    model_config = ConfigDict(extra="allow")

    checkin: str
    checkout: str


class Booking(BaseModel):
    model_config = ConfigDict(extra="allow")

    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    bookingid: int
    booking: Booking
