from pydantic import BaseModel
from uuid import UUID


class ReserveSeatSchema(BaseModel):
    event_id: int
    seat_id: int


class ReservationResponseSchema(BaseModel):
    reservation_id: str
    expires_in_seconds: int = 600


class PaymentInitRequest(BaseModel):
    event_id: int
    seat_id: int


class PaymentInitResponse(BaseModel):
    payment_id: UUID
    payment_url: str
    status: str = "PENDING"


class WebhookRequest(BaseModel):
    payment_id: UUID
    status: str