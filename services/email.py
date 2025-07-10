import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.config import settings
from app.db.crud.user import get_user_by_email

async def send_verification_email(email: str, db: Session):
    user = get_user_by_email(db, email)
    if not user:
        raise ValueError("User not found")
    
    if user.is_verified:
        raise ValueError("Email already verified")

    message = MIMEMultipart()
    message["From"] = settings.EMAIL_FROM
    message["To"] = email
    message["Subject"] = "Verify your LeadMagic account"

    verification_url = f"{settings.BASE_URL}/api/email/verify/{user.verification_token}"
    
    html = f"""
    <html>
        <body>
            <h2>Welcome to LeadMagic!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>If you didn't create this account, please ignore this email.</p>
        </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")