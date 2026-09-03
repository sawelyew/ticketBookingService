from typing import Annotated
from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.booking import (
    ReservationResponseSchema,
    ReserveSeatSchema,
    PaymentInitRequest,
    PaymentInitResponse,
    WebhookRequest
)
from app.services.booking_service import BookingService


router = APIRouter(prefix="/bookings", tags=["Booking"])


@router.post("/reserve", status_code=status.HTTP_201_CREATED)
async def reserve_seat(
        schema: ReserveSeatSchema,
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> ReservationResponseSchema:
    service = BookingService(session, redis)
    return await service.reserve_seat(current_user.id, schema)


@router.delete("/reserve/{event_id}/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
        event_id: int,
        seat_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)],
):
    service = BookingService(session, redis)
    return await service.cancel_reservation(
        event_id=event_id,
        seat_id=seat_id,
        user_id=current_user.id,
    )


@router.post("/pay")
async def initiate_payment(
    payload: PaymentInitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> PaymentInitResponse:
    service = BookingService(session=session, redis=redis)
    return await service.initiate_payment(
        payload=payload,
        user_id=current_user.id,
    )


@router.post("/webhook")
async def payment_webhook(
    payload: WebhookRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    service = BookingService(session=session, redis=redis)
    return await service.process_bank_webhook(
        payment_id=payload.payment_id,
        payment_status=payload.status,
    )