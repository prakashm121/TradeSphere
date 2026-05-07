from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings

# ??? Use settings (NO os.getenv)
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)


async def send_verification_email(email: EmailStr, token: str):
    verification_link = f"{settings.VERIFICATION_BASE_URL.rstrip('/')}/auth/verify?token={token}"
    
    # ??? Mock mode (same behavior, just using settings instead of os.getenv)
    if settings.MOCK_EMAIL:
        print(f"Mock Email: Verification link for {email} is {verification_link}")
        return

    if not all([settings.MAIL_SERVER, settings.MAIL_USERNAME, settings.MAIL_PASSWORD, settings.MAIL_FROM]):
        raise ValueError("Email settings are incomplete. Configure mail env vars or set MOCK_EMAIL=true.")

    message = MessageSchema(
        subject="Verify your TradeSphere account",
        recipients=[email],
        body=f"Click the link to verify your account: {verification_link}",
        subtype=MessageType.plain
    )

    await fm.send_message(message)