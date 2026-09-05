from fastapi import APIRouter, Depends, Query
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.dependencies import get_current_user
from app.schemas.user import UserProfileSchema
from app.schemas.ticket import PaginatedBookingSchema, ActiveTicketResponseSchema
from app.models.user import User
from app.services.ticket_service import TicketService
from app.services.s3_service import s3_service
from app.services.redis_service import RedisService

router = APIRouter(prefix="/users", tags=["Users"])

logger = logging.getLogger("uvicorn.error")


@router.get("/me")
async def get_profile(
        current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfileSchema:
    return current_user


@router.get("/me/tickets/active")
async def get_active_tickets(
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> ActiveTicketResponseSchema:
# ):
    service = TicketService(session, redis=redis)
    tickets = await service.get_active_tickets(current_user.id)
    return tickets


@router.get("/me/tickets/history")
async def get_active_tickets_history(
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, lt=100)] = 10,
) -> PaginatedBookingSchema:
    service = TicketService(session, redis=redis)
    bookings = await service.get_tickets_history(
        current_user.id,
        page,
        page_size
    )
    return bookings


@router.get("/me/tickets/{ticket_id}/download")
async def download_ticket_file(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    ticket_service = TicketService(session, s3_service, redis=redis)

    download_url = await ticket_service.get_ticket_download_url(
        ticket_id=ticket_id,
        user_id=current_user.id,
    )

    return {"download_url": download_url}