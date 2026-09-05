import taskiq_aio_pika
from app.core.config import settings


broker = taskiq_aio_pika.AioPikaBroker(
    url=settings.RABBITMQ_URL,
)

import app.tasks
