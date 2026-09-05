import random
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_password,
    decode_token
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    UserCreateSchema,
    UserReadSchema,
    VerifyEmailSchema,
    TokenSchema,
    RefreshTokenInputSchema
)
from app.tasks import send_otp_email


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.user_repo = UserRepository(session)
        self.redis = redis

    async def register_user(self, user_input: UserCreateSchema) -> UserReadSchema:
        existing_user = await self.user_repo.get_by_email(user_input.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = hash_password(user_input.password)

        user = await self.user_repo.create(
            email=user_input.email,
            hashed_password=hashed_password,
        )

        otp_code = f"{random.randint(100000, 999999)}"

        await self.redis.set(
            name=f"email_verification:{user.id}",
            value=otp_code,
            ex=600,
        )
        
        await send_otp_email.kiq(user_input.email, otp_code)

        return UserReadSchema.model_validate(user)


    async def verify_email(self, verify_data: VerifyEmailSchema) -> dict:
        redis_key = f"email_verification:{verify_data.user_id}"
        saved_code = await self.redis.get(redis_key)

        if not saved_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired or does not exist",
            )

        if saved_code != verify_data.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        user = await self.user_repo.get_by_id(verify_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )

        await self.user_repo.verify_user(user)
        await self.redis.delete(redis_key)

        return {"message": "Email successfully verified"}


    async def login_user(self, email: str, password: str) -> TokenSchema:

        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        refresh_token, jti = create_refresh_token(data={"sub": str(user.id)})

        await self.redis.set(
            name=f"refresh_token:{user.id}:{jti}",
            value="true",
            ex=604800,
        )

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
        )


    async def refresh_tokens(self, refresh_data: RefreshTokenInputSchema) -> TokenSchema:
        payload = decode_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        redis_key = f"refresh_token:{user_id}:{jti}"
        is_token_valid = await self.redis.get(redis_key)

        if not is_token_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or revoked",
            )

        await self.redis.delete(redis_key)

        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or unverified",
            )

        new_access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        new_refresh_token, new_jti = create_refresh_token(data={"sub": str(user.id)})

        await self.redis.set(
            name=f"refresh_token:{user.id}:{new_jti}",
            value="true",
            ex=604800,
        )

        return TokenSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )