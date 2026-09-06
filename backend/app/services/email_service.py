import logging
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_BRAND = {
    "primary": "#111A38",
    "background": "#EAF7FB",
    "surface": "#FFFFFF",
    "pink": "#F3A6B8",
    "text_muted": "#65758B",
    "border": "#D5E4EA",
}


async def _send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send one HTML email over STARTTLS. Fails silently (logged, not raised) when
    SMTP isn't configured or the send itself fails — matches this codebase's existing
    fail-safe pattern for optional external services (see llm_synthesizer.py): a
    missing/broken mail provider degrades the feature, it never crashes the request
    that queued it. Callers always run this via BackgroundTasks, so there's no
    response to fail regardless."""
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured — skipping email to %s (%s)", to_email, subject)
        return

    message = EmailMessage()
    message["From"] = formataddr((settings.app_name, settings.emails_from or settings.smtp_user))
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("This email requires an HTML-capable client to view.")
    message.add_alternative(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
    except Exception:
        logger.exception("Failed to send email to %s (%s)", to_email, subject)


def _button_email_html(*, preheader: str, heading: str, body_text: str, button_label: str, link: str) -> str:
    """Shared layout for both templates — inline styles throughout, since email
    clients strip <style> blocks and don't reliably support external/app CSS
    variables, so the brand palette is hardcoded here rather than referencing
    design-theme.md's CSS custom properties directly."""
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:{_BRAND["background"]};font-family:Arial,Helvetica,sans-serif;">
    <span style="display:none;font-size:1px;color:{_BRAND["background"]};line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preheader}</span>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background:{_BRAND["surface"]};border-radius:12px;overflow:hidden;">
            <tr>
              <td style="background:{_BRAND["primary"]};padding:24px 32px;">
                <span style="color:{_BRAND["surface"]};font-size:18px;font-weight:700;letter-spacing:0.02em;">AniFerret</span>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;">
                <h1 style="margin:0 0 12px;color:{_BRAND["primary"]};font-size:20px;">{heading}</h1>
                <p style="margin:0 0 24px;color:{_BRAND["text_muted"]};font-size:14px;line-height:1.6;">{body_text}</p>
                <table role="presentation" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="border-radius:8px;background:{_BRAND["pink"]};">
                      <a href="{link}" style="display:inline-block;padding:12px 28px;color:{_BRAND["primary"]};font-size:14px;font-weight:600;text-decoration:none;">{button_label}</a>
                    </td>
                  </tr>
                </table>
                <p style="margin:24px 0 0;color:{_BRAND["text_muted"]};font-size:12px;line-height:1.6;">
                  Button not working? Copy and paste this link into your browser:<br />
                  <a href="{link}" style="color:{_BRAND["primary"]};word-break:break-all;">{link}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 32px;border-top:1px solid {_BRAND["border"]};">
                <p style="margin:0;color:{_BRAND["text_muted"]};font-size:11px;">If you didn't request this, you can safely ignore this email.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


async def send_verification_email(to_email: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.frontend_url}/verify-email?token={token}"
    html = _button_email_html(
        preheader="Verify your email to start using AniFerret.",
        heading="Verify your email address",
        body_text=(
            "Thanks for signing up for AniFerret. Click the button below to verify "
            "your email and activate your account. This link expires in 24 hours."
        ),
        button_label="Verify Email",
        link=link,
    )
    await _send_email(to_email, "Verify your AniFerret account", html)


async def send_password_reset_email(to_email: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.frontend_url}/reset-password?token={token}"
    html = _button_email_html(
        preheader="Reset your AniFerret password.",
        heading="Reset your password",
        body_text=(
            "We received a request to reset your AniFerret password. Click the "
            "button below to choose a new one. This link expires in 1 hour."
        ),
        button_label="Reset Password",
        link=link,
    )
    await _send_email(to_email, "Reset your AniFerret password", html)
