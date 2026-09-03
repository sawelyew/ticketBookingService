from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TicketReadSchema(BaseModel):
    ticket_id: int
    event_title: str
    event_date: datetime
    venue_name: str
    row_number: int
    seat_number: int
    pdf_download_url: str

    model_config = ConfigDict(from_attributes=True)


class TicketHistoryItemSchema(BaseModel):
    booking_id: int
    ticket_id: int | None = None
    event_title: str
    event_date: datetime
    venue_name: str
    row_number: int
    seat_number: int
    status: str
    price: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBookingSchema(BaseModel):
    items: list[TicketHistoryItemSchema]
    total: int
    page: int
    page_size: int
    pages: int


class ActiveTicketResponseSchema(BaseModel):
    tickets: list[TicketReadSchema]