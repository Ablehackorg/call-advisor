# app/mailer.py
import smtplib
from email.mime.text import MIMEText

from .config import settings
from .logging_conf import logger


def send_recommendation_email(body: str) -> None:
    """
    Отправляет текст рекомендации на RESULT_EMAIL из настроек.
    """
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = "Рекомендация по звонку"
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = settings.RESULT_EMAIL

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, [settings.RESULT_EMAIL], msg.as_string())

        logger.info("Email with recommendation sent to %s", settings.RESULT_EMAIL)
    except Exception as e:
        logger.exception("Failed to send recommendation email: %s", e)
        raise
