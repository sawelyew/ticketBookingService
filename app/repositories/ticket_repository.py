from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from uuid import UUID
from typing import Optional

from app.models.booking import Booking
from app.models.event import Event
from app.models.seat import Seat
from app.models.ticket import Ticket



class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_user_tickets(self, user_id: int) -> list[Ticket]:
        now = datetime.now(timezone.utc)

        stmt = (
            select(Ticket)
            .join(Ticket.booking)
            .join(Booking.seat)
            .join(Seat.event)
            .where(
                Booking.user_id == user_id,
                Booking.status == "CONFIRMED",
                Event.event_date > now
            )
            .options(
                joinedload(Ticket.booking)
                .joinedload(Booking.seat)
                .joinedload(Seat.event)
            )
            .order_by(Event.event_date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())


    async def get_tickets_history(
            self, user_id: int, page: int = 1, page_size: int = 10
    ) -> tuple[list[Booking], int]:

        now = datetime.now(timezone.utc)

        history_filter = (Booking.user_id == user_id) & (
            or_(
                Event.event_date <= now,
                Booking.status.in_(["CANCELLED"])
            )
        )

        count_stmt = (
            select(func.count(Booking.id))
            .join(Booking.seat)
            .join(Seat.event)
            .where(history_filter)
        )
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            select(Booking)
            .join(Booking.seat)
            .join(Seat.event)
            .outerjoin(Booking.ticket)
            .where(history_filter)
            .options(
                joinedload(Booking.seat).joinedload(Seat.event),
                joinedload(Booking.ticket),
            )
            .order_by(Booking.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(stmt)
        bookings = list(result.scalars().all())

        return bookings, total


    async def get_by_id_with_booking(self, ticket_id: int) -> Optional[Ticket]:
        stmt = (
            select(Ticket)
            .options(joinedload(Ticket.booking))
            .where(Ticket.id == ticket_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()