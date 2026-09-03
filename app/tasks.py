import io
import os
import qrcode
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.taskiq import broker
from app.services.s3_service import S3Service
from app.core.config import settings


mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=int(settings.MAIL_PORT),
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

s3_service = S3Service()


@broker.task
async def process_ticket_generation(
    booking_id: int,
    ticket_id: str,
    recipient_email: str,
) -> None:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(ticket_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_bytes = buffer.getvalue()

    object_name = f"qr_codes/ticket_{ticket_id}.png"

    await s3_service.upload_file(
        file_data=qr_bytes,
        object_name=object_name,
        content_type="image/png",
    )

    await send_ticket_email.kiq(
        booking_id=booking_id,
        ticket_id=ticket_id,
        recipient_email=recipient_email,
        object_name=object_name,
    )


@broker.task
async def send_ticket_email(
    booking_id: int,
    ticket_id: str,
    recipient_email: str,
    object_name: str,
) -> None:
    qr_bytes = await s3_service.get_file_bytes(object_name)

    attachment = UploadFile(
        filename=f"ticket_{booking_id}_qr.png",
        file=io.BytesIO(qr_bytes),
        headers={"content-type": "image/png"},
    )

    html_content = f"""
    <h3>Ваш билет #{booking_id} успешно оформлен!</h3>
    <p><b>ID билета:</b> {ticket_id}</p>
    <p>QR-код во вложении к этому письму.</p>
    """

    message = MessageSchema(
        subject=f"Ваш билет #{booking_id}",
        recipients=[recipient_email],
        body=html_content,
        subtype=MessageType.html,
        attachments=[attachment],
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)