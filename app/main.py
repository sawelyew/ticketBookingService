from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1 import auth_router, user_router, event_router, booking_router
from app.core.taskiq import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(event_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")