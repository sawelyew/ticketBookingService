from pydantic import BaseModel, ConfigDict
from datetime import datetime

class EventShortSchema(BaseModel):
    id: int
    title: str
    description: str | None
    event_date: datetime
    venue_name: str
    total_seats: int

    model_config = ConfigDict(from_attributes=True)


class EventDetailSchema(EventShortSchema):
    pass

class PaginatedEventsSchema(BaseModel):
    items: list[EventShortSchema]
    total: int
    page: int
    page_size: int
    pages: int


class EventResponseModel(BaseModel):
    event_details: EventDetailSchema