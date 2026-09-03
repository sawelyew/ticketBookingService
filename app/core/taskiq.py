import taskiq_aio_pika
from taskiq import TaskiqEvents, TaskiqState
from app.core.config import settings


broker = taskiq_aio_pika.AioPikaBroker(
    url=settings.RABBITMQ_URL,
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    pass


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    pass