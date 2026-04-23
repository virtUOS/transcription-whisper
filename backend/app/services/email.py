import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailConfigError(Exception):
    """Raised when SMTP settings are missing or incomplete."""


def _body_text(invite_url: str) -> str:
    return (
        "You have been invited to the Transcription service.\n\n"
        f"Click the link below to set up your account:\n\n{invite_url}\n\n"
        "This link expires in 7 days. If you did not expect this email, you can ignore it.\n"
    )


def _body_html(invite_url: str) -> str:
    return (
        "<p>You have been invited to the Transcription service.</p>"
        f'<p><a href="{invite_url}">Click here to set up your account</a></p>'
        f'<p>Or paste this link into your browser:<br><code>{invite_url}</code></p>'
        "<p>This link expires in 7 days. If you did not expect this email, you can ignore it.</p>"
    )


def send_invitation_email(*, to_email: str, invite_url: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise EmailConfigError(
            "SMTP_HOST and SMTP_FROM must be set to send invitation emails"
        )

    msg = EmailMessage()
    msg["Subject"] = "You have been invited to the Transcription service"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(_body_text(invite_url))
    msg.add_alternative(_body_html(invite_url), subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
        if settings.SMTP_STARTTLS:
            s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)
