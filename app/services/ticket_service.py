from sqlalchemy.ext.asyncio import AsyncSession
import math
from fastapi import HTTPException, status
from redis.asyncio import Redis


from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import (TicketReadSchema, TicketHistoryItemSchema,
                                PaginatedBookingSchema, ActiveTicketResponseSchema)
from app.services.s3_service import S3Service
from app.services.redis_service import RedisService


class TicketService:
    def __init__(self, session: AsyncSession, s3_service: S3Service = None, redis: Redis = None):
        self.ticket_repository = TicketRepository(session)
        self.s3_service = s3_service
        self.redis_service = RedisService(redis)


    async def get_active_tickets(self, user_id: int) -> ActiveTicketResponseSchema:
        cache_key = f"user:{user_id}:tickets:active"

        cached_data = await self.redis_service.redis.get(cache_key)
        if cached_data:
            return ActiveTicketResponseSchema.model_validate_json(cached_data)


        tickets = await self.ticket_repository.get_active_user_tickets(user_id)

        response = []
        for ticket in tickets:
            booking = ticket.booking
            seat = booking.seat
            event = seat.event

            response.append(
                TicketReadSchema(
                    ticket_id=ticket.id,
                    event_title=event.title,
                    event_date=event.event_date,
                    venue_name=event.venue_name,
                    row_number=seat.row_number,
                    seat_number=seat.seat_number,
                    pdf_download_url=f"/api/v1/users/me/tickets/{ticket.id}/download",
                )
            )

        result = ActiveTicketResponseSchema(tickets=response)

        await self.redis_service.redis.set(
            cache_key,
            result.model_dump_json(),
            ex=600
        )

        return result

    async def get_tickets_history(
            self, user_id: int, page: int = 1, page_size: int = 10
    ) -> PaginatedBookingSchema:
        cache_key = f"user:{user_id}:tickets:history:p{page}:s{page_size}"
        cached_data = await self.redis_service.redis.get(cache_key)
        if cached_data:
            return PaginatedBookingSchema.model_validate_json(cached_data)

        bookings, total = await self.ticket_repository.get_tickets_history(user_id, page, page_size)

        items = []
        for booking in bookings:
            seat = booking.seat
            event = seat.event
            items.append(
                TicketHistoryItemSchema(
                    booking_id=booking.id,
                    ticket_id=booking.ticket.id if booking.ticket else None,
                    event_title=event.title,
                    event_date=event.event_date,
                    venue_name=event.venue_name,
                    row_number=seat.row_number,
                    seat_number=seat.seat_number,
                    status=booking.status,
                    price=float(seat.price),
                    created_at=booking.created_at,
                )
            )

        pages = math.ceil(total / page_size) if total > 0 else 1

        result = PaginatedBookingSchema(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

        await self.redis_service.redis.set(
            cache_key,
            result.model_dump_json(),
            ex=180,
        )

        return result


    async def get_ticket_download_url(
            self, ticket_id: int, user_id: int
    ) -> str:
        cache_key = f"user:{user_id}:ticket:{ticket_id}:download_url"
        cached_data = await self.redis_service.redis.get(cache_key)
        if cached_data:
            return cached_data.decode() if isinstance(cached_data, bytes) else cached_data

        ticket = await self.ticket_repository.get_by_id_with_booking(ticket_id)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        if ticket.booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to download this ticket",
            )

        object_name = f"qr_codes/ticket_{ticket_id}.png"

        download_url = await self.s3_service.get_presigned_url(
            object_name=object_name,
            expires_in=900
        )

        await self.redis_service.redis.set(
            cache_key,
            download_url,
            ex=840,
        )

        return download_url