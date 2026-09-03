import math
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.repositories.event_repository import EventRepository
from app.schemas.event import EventDetailSchema, EventShortSchema, PaginatedEventsSchema
from app.repositories.seat_repository import SeatRepository
from app.schemas.seat import SeatStatus, SeatStatusSchema
from app.services.redis_service import RedisService


class EventService:
    def __init__(self, session: AsyncSession, redis: Redis = None):
        self.session = session
        self.event_repository = EventRepository(session)
        self.seat_repository = SeatRepository(session)
        self.redis_service = RedisService(redis) if redis else None


    async def get_all_events(
            self,
            date_from: datetime | None,
            date_to: datetime | None,
            venue_name: str | None,
            search: str | None,
            page: int,
            page_size: int,
    ) -> PaginatedEventsSchema:
        events, total = await self.event_repository.get_events(
            date_from=date_from,
            date_to=date_to,
            venue_name=venue_name,
            search=search,
            page=page,
            page_size=page_size,
        )

        items = [EventShortSchema.model_validate(event) for event in events]
        pages = math.ceil(total / page_size) if total > 0 else 1

        return PaginatedEventsSchema(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


    async def get_event_details(self, event_id: int) -> EventDetailSchema:
        event = await self.event_repository.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return EventDetailSchema.model_validate(event)


    async def get_event_seats(self, event_id: int) -> list[SeatStatusSchema]:
        event = await self.event_repository.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        seats_with_status = await self.seat_repository.get_seats_with_confirmed_bookings(event_id)

        locked_seat_ids: set[int] = set()
        if self.redis_service:
            locked_seat_ids = await self.redis_service.get_locked_seats(event_id)

        result = []
        for seat, is_sold in seats_with_status:
            if is_sold:
                seat_status = SeatStatus.SOLD
            elif seat.id in locked_seat_ids:
                seat_status = SeatStatus.LOCKED
            else:
                seat_status = SeatStatus.AVAILABLE

            result.append(
                SeatStatusSchema(
                    id=seat.id,
                    row_number=seat.row_number,
                    seat_number=seat.seat_number,
                    price=seat.price,
                    status=seat_status,
                )
            )

        return result