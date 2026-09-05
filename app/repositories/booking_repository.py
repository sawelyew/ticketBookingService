import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import Optional
from fastapi import HTTPException, status
import hmac
import hashlib

from app.models.booking import Booking, BookingStatus
from app.models.event import Event
from app.models.seat import Seat
from app.models.ticket import Ticket
from app.models.payment import PaymentTransaction, PaymentStatus
from app.core.config import settings


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def seat_is_sold(self, seat_id: int) -> bool:
        query = select(Booking.id).where(
            Booking.seat_id == seat_id,
            Booking.status == "CONFIRMED",
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


    async def event_exists(self, event_id: int) -> bool:
        stmt = select(Event.id).where(Event.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


    async def get_seat_by_id_and_event(
            self,
            seat_id: int,
            event_id: int
    ) -> Seat | None:
        stmt = select(Seat).where(
            Seat.id == seat_id,
            Seat.event_id == event_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def create_pending_payment_and_booking(
            self,
            user_id: int,
            seat_id: int,
    ) -> PaymentTransaction:
        existing_booking = await self.session.scalar(
            select(Booking).where(
                Booking.seat_id == seat_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            )
        )
        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This seat is already booked in the system"
            )

        async with self.session.begin_nested():
            seat = await self.session.get(Seat, seat_id)
            if not seat:
                raise HTTPException(status_code=404, detail="Seat not found")

            booking = Booking(
                user_id=user_id,
                seat_id=seat_id,
                status="PENDING",
            )
            self.session.add(booking)
            await self.session.flush()

            payment = PaymentTransaction(
                id=uuid.uuid4(),
                booking_id=booking.id,
                amount=seat.price,
                status=PaymentStatus.PENDING,
            )
            self.session.add(payment)

        await self.session.commit()
        await self.session.refresh(payment)
        return payment


    async def get_payment_with_booking(
            self,
            payment_id: uuid.UUID
    ) -> Optional[PaymentTransaction]:
        stmt = (
            select(PaymentTransaction)
            .options(
                joinedload(PaymentTransaction.booking).options(
                    joinedload(Booking.seat),
                    selectinload(Booking.user),
                )
            )
            .where(PaymentTransaction.id == payment_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def confirm_payment_and_create_ticket(
            self,
            payment: PaymentTransaction,
            booking: Booking
    ) -> Ticket:
        async with self.session.begin_nested():
            payment.status = PaymentStatus.SUCCESS
            booking.status = BookingStatus.CONFIRMED
            b_id = booking.id

            ticket = Ticket(
                booking_id=b_id,
            )
            self.session.add(ticket)
            await self.session.flush()

            secret_bytes = settings.SECRET_KEY.encode("utf-8")
            data_to_sign = f"ticket:{ticket.id}:booking:{booking.id}".encode("utf-8")

            ticket.signature_hash = hmac.new(
                secret_bytes,
                data_to_sign,
                hashlib.sha256
            ).hexdigest()

        await self.session.commit()
        return ticket


    async def mark_payment_failed(
            self,
            payment: PaymentTransaction,
            booking: Booking
    ) -> None:
        payment.status = PaymentStatus.FAILED
        booking.status = BookingStatus.CANCELLED
        await self.session.commit()