from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.booking import Booking


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = UniqueConstraint("event_id", "row_number", "seat_number", name="uq_event_row_seat"),

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    event: Mapped["Event"] = relationship(back_populates="seats")
    booking: Mapped["Booking | None"] = relationship(back_populates="seat", uselist=False)