from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models import Seat



class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_events(
            self,
            date_from: datetime | None = None,
            date_to: datetime | None = None,
            venue_name: str | None = None,
            search: str | None = None,
            page: int = 1,
            page_size: int = 10,
    ) -> tuple[list[Event], int]:
        filters = []

        if date_from:
            filters.append(Event.event_date >= date_from)
        if date_to:
            filters.append(Event.event_date <= date_to)
        if venue_name:
            filters.append(Event.venue_name.ilike(f"%{venue_name}%"))
        if search:
            filters.append(
                or_(
                    Event.title.ilike(f"%{search}%"),
                    Event.description.ilike(f"%{search}%"),
                )
            )

        count_stmt = select(func.count(Event.id))
        if filters:
            count_stmt = count_stmt.where(*filters)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = select(Event)
        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(Event.event_date.asc()).offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        events = list(result.scalars().all())

        return events, total


    async def get_event(self, event_id: int) -> Event | None:
        stmt = select(Event).where(Event.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()