import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.logging import logger


def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.SMTP_HOST:
        logger.warning(f"SMTP not configured — skipping email to {to}: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, to, msg.as_string())

        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def send_password_reset_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <h2>Password Reset</h2>
    <p>Click the link below to reset your password. This link expires in <strong>1 hour</strong>.</p>
    <p><a href="{url}">{url}</a></p>
    <p>If you did not request this, you can safely ignore this email.</p>
    """
    return send_email(to, "Reset your password", html)


def send_verification_email(to: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <h2>Verify your email address</h2>
    <p>Click the link below to activate your account. This link expires in <strong>24 hours</strong>.</p>
    <p><a href="{url}">{url}</a></p>
    """
    return send_email(to, "Verify your email", html)
