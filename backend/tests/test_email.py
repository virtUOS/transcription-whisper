import pytest
from unittest.mock import MagicMock, patch

from app.services.email import send_invitation_email, EmailConfigError


def test_send_invitation_email_uses_settings(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.SMTP_HOST = "smtp.example.com"
    mock_settings.SMTP_PORT = 587
    mock_settings.SMTP_STARTTLS = True
    mock_settings.SMTP_USER = "u"
    mock_settings.SMTP_PASSWORD = "p"
    mock_settings.SMTP_FROM = "noreply@example.com"

    fake_smtp = MagicMock()
    fake_smtp.__enter__.return_value = fake_smtp

    with patch("app.services.email.settings", mock_settings):
        with patch("app.services.email.smtplib.SMTP", return_value=fake_smtp):
            send_invitation_email(
                to_email="new@example.com",
                invite_url="https://app.example.com/invite/tw_inv_xyz",
            )

    fake_smtp.starttls.assert_called_once()
    fake_smtp.login.assert_called_once_with("u", "p")
    fake_smtp.send_message.assert_called_once()
    msg = fake_smtp.send_message.call_args[0][0]
    assert msg["To"] == "new@example.com"
    assert msg["From"] == "noreply@example.com"
    assert "https://app.example.com/invite/tw_inv_xyz" in str(msg)


def test_send_invitation_email_skips_starttls_when_disabled(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.SMTP_HOST = "relay.internal"
    mock_settings.SMTP_PORT = 25
    mock_settings.SMTP_STARTTLS = False
    mock_settings.SMTP_USER = ""
    mock_settings.SMTP_PASSWORD = ""
    mock_settings.SMTP_FROM = "noreply@internal"

    fake_smtp = MagicMock()
    fake_smtp.__enter__.return_value = fake_smtp

    with patch("app.services.email.settings", mock_settings):
        with patch("app.services.email.smtplib.SMTP", return_value=fake_smtp):
            send_invitation_email(
                to_email="x@internal",
                invite_url="https://app.internal/invite/tw_inv_a",
            )

    fake_smtp.starttls.assert_not_called()
    fake_smtp.login.assert_not_called()
    fake_smtp.send_message.assert_called_once()


def test_send_invitation_email_raises_when_smtp_unset(monkeypatch):
    mock_settings = MagicMock()
    mock_settings.SMTP_HOST = ""
    mock_settings.SMTP_FROM = ""

    with patch("app.services.email.settings", mock_settings):
        with pytest.raises(EmailConfigError):
            send_invitation_email(
                to_email="x@example.com",
                invite_url="https://app.example.com/invite/tw_inv_y",
            )
