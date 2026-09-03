from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict


class SeatStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    SOLD = "SOLD"


class SeatStatusSchema(BaseModel):
    id: int
    row_number: int
    seat_number: int
    price: Decimal
    status: SeatStatus

    model_config = ConfigDict(from_attributes=True)


class SeatResponseSchema(BaseModel):
    seats: list[SeatStatusSchema]