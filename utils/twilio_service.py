from twilio.rest import Client
from core.config import settings

client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_sms(phone_number: str, otp: str):

    message = client.messages.create(
        body=f"Your OTP is {otp}. It expires in 5 minutes.If you did not request this,please ignore.Do not share this OTP with anyone.This is a secure code.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number
    )

    return message.sid