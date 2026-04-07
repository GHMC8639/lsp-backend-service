from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True
)


async def send_otp_email(email: str, otp: str):
    message = MessageSchema(
        subject="Email Verification OTP",
        recipients=[email],
        body=f"Your OTP is: {otp}",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
