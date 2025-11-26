#import aiosmtplib
from email.message import EmailMessage


async def send_otp_email(email: str, otp: str):
    message = EmailMessage()
    message["From"] = "noreply@example.com"
    message["To"] = email
    message["Subject"] = "Your OTP Verification Code"
    message.set_content(f"Your OTP code is: {otp}")

    # Example SMTP config — replace with real values
    # await aiosmtplib.send(
    #     message,
    #     hostname="smtp.example.com",
    #     port=587,
    #     username="username",
    #     password="password",
    #     start_tls=True,
    # )
