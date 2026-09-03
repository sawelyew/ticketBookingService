from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat


class SeatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_seats_with_confirmed_bookings(self, event_id: int) -> list[tuple[Seat, bool]]:
        stmt = (
            select(
                Seat,
                (Booking.id.is_not(None)).label("is_sold")
            )
            .outerjoin(
                Booking,
                (Booking.seat_id == Seat.id) & (Booking.status == "CONFIRMED")
            )
            .where(Seat.event_id == event_id)
            .order_by(Seat.row_number.asc(), Seat.seat_number.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.all())