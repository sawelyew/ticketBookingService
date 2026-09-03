from fastapi import FastAPI

from app.api.v1 import auth_router, user_router, event_router, booking_router


app = FastAPI()

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(event_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")