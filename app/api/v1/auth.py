from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.auth import UserCreateSchema, UserReadSchema, VerifyEmailSchema, RefreshTokenInputSchema
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
        user_input: UserCreateSchema,
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)]
) -> UserReadSchema:
    auth_service = AuthService(session, redis)
    return await auth_service.register_user(user_input)


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
)
async def verify_email(
        verify_data: VerifyEmailSchema,
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)]
):
    auth_service = AuthService(session, redis)
    return await auth_service.verify_email(verify_data)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(get_db)],
        redis: Annotated[Redis, Depends(get_redis)]
):
    auth_service = AuthService(session, redis)
    return await auth_service.login_user(
        email=form_data.username,
        password=form_data.password
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
)
async def refresh(refresh_data: RefreshTokenInputSchema,
                  session: Annotated[AsyncSession, Depends(get_db)],
                  redis: Annotated[Redis, Depends(get_redis)]
):
    auth_service = AuthService(session, redis)
    return await auth_service.refresh_tokens(refresh_data)