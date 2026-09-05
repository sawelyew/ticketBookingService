from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.event import PaginatedEventsSchema, EventResponseModel
from app.services.event_service import EventService
from app.schemas.seat import SeatResponseSchema

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/")
async def get_all_events(
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    date_from: Annotated[datetime | None, Query(description="Фильтр: от даты")] = None,
    date_to: Annotated[datetime | None, Query(description="Фильтр: до даты")] = None,
    venue_name: Annotated[str | None, Query(description="Фильтр по площадке")] = None,
    search: Annotated[str | None, Query(description="Поиск по title и description")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PaginatedEventsSchema:
    service = EventService(session, redis)
    events = await service.get_all_events(
        date_from=date_from,
        date_to=date_to,
        venue_name=venue_name,
        search=search,
        page=page,
        page_size=page_size,
    )
    return events


@router.get("/{event_id}")
async def get_event(
        event_id: int,
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> EventResponseModel:
    service = EventService(session, redis)
    event = await service.get_event_details(event_id)
    return {"event_details": event}


@router.get("/{event_id}/seats")
async def get_seats(
        event_id: int,
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> SeatResponseSchema:
    service = EventService(session, redis)
    seats = await service.get_event_seats(event_id)
    return {"seats": seats}