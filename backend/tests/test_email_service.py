"""Unit tests for email_service._send_email — sends via Resend's HTTPS API rather
than raw SMTP (see the function's docstring: Railway was confirmed, via a real
deploy-log SMTPConnectTimeoutError that persisted even after forcing IPv4, to be
silently black-holing outbound traffic on SMTP ports). Every I/O boundary
(httpx.AsyncClient) is mocked, since real network access is never allowed in
tests — see conftest.py's _no_live_email_calls fixture, which these tests
intentionally bypass by re-patching get_settings themselves.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services import email_service


class _ResendSettings:
    resend_api_key = "re_test_123"
    emails_from = "noreply@aniferret.app"
    app_name = "AniFerret"


class _NoResendSettings:
    resend_api_key = ""
    emails_from = ""
    app_name = "AniFerret"


def _mock_client(response: MagicMock) -> MagicMock:
    """Builds a mock matching `async with httpx.AsyncClient(...) as client:` —
    __aenter__ must return an object whose .post() is itself awaitable."""
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=client)
    context_manager.__aexit__ = AsyncMock(return_value=False)
    return context_manager, client


async def test_send_email_posts_to_resend_with_expected_payload(monkeypatch) -> None:
    monkeypatch.setattr(email_service, "get_settings", lambda: _ResendSettings())

    response = MagicMock()
    response.raise_for_status = MagicMock()
    context_manager, client = _mock_client(response)

    with patch.object(email_service.httpx, "AsyncClient", return_value=context_manager):
        await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    client.post.assert_awaited_once()
    args, kwargs = client.post.await_args
    assert args[0] == email_service._RESEND_API_URL
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_123"
    assert kwargs["json"]["to"] == ["someone@example.com"]
    assert kwargs["json"]["subject"] == "Subject"
    assert kwargs["json"]["html"] == "<p>body</p>"
    assert "AniFerret" in kwargs["json"]["from"]
    assert "noreply@aniferret.app" in kwargs["json"]["from"]
    response.raise_for_status.assert_called_once()


async def test_send_email_noop_when_resend_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(email_service, "get_settings", lambda: _NoResendSettings())

    with patch.object(email_service.httpx, "AsyncClient") as async_client_cls:
        await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    async_client_cls.assert_not_called()


async def test_send_email_swallows_http_errors(monkeypatch) -> None:
    """Mirrors the real-world failure this design must survive: a bad/expired API
    key, a Resend outage, or (previously) a network-level block. _send_email's
    fail-safe design must swallow this — never raise into the caller, since it
    always runs via BackgroundTasks with no response left to fail."""
    monkeypatch.setattr(email_service, "get_settings", lambda: _ResendSettings())

    response = MagicMock()
    response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock())
    )
    context_manager, client = _mock_client(response)

    with patch.object(email_service.httpx, "AsyncClient", return_value=context_manager):
        await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    client.post.assert_awaited_once()
