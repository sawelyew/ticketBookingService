from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.seat import Seat
    from app.models.payment import PaymentTransaction
    from app.models.ticket import Ticket


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="CASCADE"), nullable=False, unique=True)
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="bookings")
    seat: Mapped["Seat"] = relationship(back_populates="booking")
    payment_transaction: Mapped["PaymentTransaction | None"] = relationship(back_populates="booking", uselist=False)
    ticket: Mapped["Ticket | None"] = relationship(back_populates="booking", uselist=False)