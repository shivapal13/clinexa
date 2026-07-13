from fastapi_mail import FastMail,MessageSchema,ConnectionConfig,MessageType
from app.core.config import settings

conf=ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)
fast_mail=FastMail(conf)

async def send_email(
    recipients: list[str],
    subject: str,
    body: str 
):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )

    await fast_mail.send_message(message)