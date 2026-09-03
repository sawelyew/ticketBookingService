import uuid
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.booking import ReservationResponseSchema, ReserveSeatSchema, PaymentInitResponse, PaymentInitRequest
from app.repositories.booking_repository import BookingRepository
from app.services.redis_service import RedisService
from app.models.payment import PaymentTransaction, PaymentStatus
from app.tasks import process_ticket_generation



class BookingService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.booking_repository = BookingRepository(session)
        self.redis_service = RedisService(redis)

    async def reserve_seat(self, user_id: int, schema: ReserveSeatSchema) -> ReservationResponseSchema:
        if not await self.booking_repository.event_exists(schema.event_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id {schema.event_id} not found",
            )

        seat = await self.booking_repository.get_seat_by_id_and_event(
            seat_id=schema.seat_id, event_id=schema.event_id
        )
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Seat with id {schema.seat_id} not found for this event",
            )

        if await self.booking_repository.seat_is_sold(schema.seat_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seat is already sold",
            )

        lock_key = f"lock:event:{schema.event_id}:seat:{schema.seat_id}"
        is_locked = await self.redis_service.redis.set(lock_key, user_id, nx=True, ex=600)

        if not is_locked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seat is temporarily reserved by another user",
            )

        return ReservationResponseSchema(
            reservation_id=lock_key,
            expires_in_seconds=600,
        )


    async def cancel_reservation(
            self,
            event_id: int,
            seat_id: int,
            user_id: int
    ) -> None:
        lock_key = f"lock:event:{event_id}:seat:{seat_id}"

        locked_user_id = await self.redis_service.redis.get(lock_key)

        if not locked_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found or already expired",
            )

        if int(locked_user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own reservation",
            )

        await self.redis_service.redis.delete(lock_key)


    async def initiate_payment(
            self,
            payload: PaymentInitRequest,
            user_id: int
    ) -> PaymentInitResponse:
        lock_key = f"lock:event:{payload.event_id}:seat:{payload.seat_id}"
        locked_user_id = await self.redis_service.redis.get(lock_key)

        if not locked_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reservation expired or does not exist",
            )

        if int(locked_user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This seat reservation belongs to another user",
            )

        payment = await self.booking_repository.create_pending_payment_and_booking(
            user_id=user_id,
            seat_id=payload.seat_id,
        )

        return PaymentInitResponse(
            payment_id=payment.id,
            payment_url=f"https://fake-bank.com/pay/{payment.id}",
            status="PENDING",
        )


    async def process_bank_webhook(
            self,
            payment_id: uuid.UUID,
            payment_status: str
    ) -> dict:
        payment = await self.booking_repository.get_payment_with_booking(payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment transaction not found",
            )

        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already been processed",
            )

        booking = payment.booking

        if payment_status == "FAILED":
            await self.booking_repository.mark_payment_failed(payment, booking)
            return {"status": "FAILED", "detail": "Payment was declined"}

        ticket = await self.booking_repository.confirm_payment_and_create_ticket(
            payment=payment,
            booking=booking,
        )

        lock_key = f"lock:event:{booking.seat.event_id}:seat:{booking.seat_id}"
        await self.redis_service.redis.delete(lock_key)

        await process_ticket_generation.kiq(
            booking_id=booking.id,
            ticket_id=str(ticket.id),
            recipient_email=booking.user.email,
        )

        return {
            "status": "SUCCESS",
            "booking_id": booking.id,
            "ticket_id": str(ticket.id),
        }