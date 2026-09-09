"""Unit tests for email_service._send_email's connection-establishment mechanics
— specifically the IPv4-forcing fix for Railway's observed outbound IPv6
black-holing to smtp.gmail.com (see the function's docstring). Every I/O boundary
(DNS resolution, socket connect, aiosmtplib.send) is mocked, since real network
access is never allowed in tests — see conftest.py's _no_live_smtp_calls fixture,
which these tests intentionally bypass by re-patching get_settings themselves.
"""

import socket
from unittest.mock import AsyncMock, MagicMock

from app.services import email_service


class _SmtpSettings:
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "bot@example.com"
    smtp_password = "app-password"
    emails_from = ""
    app_name = "AniFerret"


def _fake_addrinfo() -> list:
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.0.1", 587))]


async def test_send_email_resolves_ipv4_and_hands_aiosmtplib_a_connected_socket(
    monkeypatch,
) -> None:
    monkeypatch.setattr(email_service, "get_settings", lambda: _SmtpSettings())

    getaddrinfo_mock = AsyncMock(return_value=_fake_addrinfo())
    sock_connect_mock = AsyncMock(return_value=None)
    send_mock = AsyncMock(return_value=({}, "OK"))

    fake_loop = MagicMock()
    fake_loop.getaddrinfo = getaddrinfo_mock
    fake_loop.sock_connect = sock_connect_mock
    monkeypatch.setattr(email_service.asyncio, "get_running_loop", lambda: fake_loop)
    monkeypatch.setattr(email_service.aiosmtplib, "send", send_mock)

    await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    getaddrinfo_mock.assert_awaited_once_with(
        "smtp.gmail.com", 587, family=socket.AF_INET, type=socket.SOCK_STREAM
    )
    sock_connect_mock.assert_awaited_once()
    connected_sock = sock_connect_mock.await_args.args[0]
    assert connected_sock.family == socket.AF_INET

    send_mock.assert_awaited_once()
    _, kwargs = send_mock.await_args
    assert kwargs["hostname"] == "smtp.gmail.com"
    assert kwargs["sock"] is connected_sock
    connected_sock.close()


async def test_send_email_closes_the_socket_if_connect_fails(monkeypatch) -> None:
    """Mirrors the real-world timeout this fix targets: getaddrinfo succeeds,
    but the connect itself hangs/fails (as IPv6 to smtp.gmail.com did on
    Railway). _send_email's fail-safe design must still swallow this — never
    raise into the caller — and must not leak the half-opened socket."""
    monkeypatch.setattr(email_service, "get_settings", lambda: _SmtpSettings())

    getaddrinfo_mock = AsyncMock(return_value=_fake_addrinfo())
    sock_connect_mock = AsyncMock(side_effect=TimeoutError("simulated black hole"))

    fake_loop = MagicMock()
    fake_loop.getaddrinfo = getaddrinfo_mock
    fake_loop.sock_connect = sock_connect_mock
    monkeypatch.setattr(email_service.asyncio, "get_running_loop", lambda: fake_loop)

    await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    sock_connect_mock.assert_awaited_once()
    connected_sock = sock_connect_mock.await_args.args[0]
    assert connected_sock.fileno() == -1


async def test_send_email_noop_when_smtp_unconfigured(monkeypatch) -> None:
    class _NoSmtpSettings:
        smtp_host = ""
        smtp_port = 587
        smtp_user = ""
        smtp_password = ""
        emails_from = ""
        app_name = "AniFerret"

    monkeypatch.setattr(email_service, "get_settings", lambda: _NoSmtpSettings())
    getaddrinfo_mock = AsyncMock()
    fake_loop = MagicMock()
    fake_loop.getaddrinfo = getaddrinfo_mock
    monkeypatch.setattr(email_service.asyncio, "get_running_loop", lambda: fake_loop)

    await email_service._send_email("someone@example.com", "Subject", "<p>body</p>")

    getaddrinfo_mock.assert_not_awaited()
