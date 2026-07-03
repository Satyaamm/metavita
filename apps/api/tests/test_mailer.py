"""Mailer tests — provider selection + request shaping (HTTP/SMTP mocked)."""

from __future__ import annotations

import pytest
from metavita_api.services import mailer as m


def test_build_mailer_selects_provider():
    assert isinstance(m.build_mailer("smtp", {"host": "h"}), m.SmtpMailer)
    assert isinstance(m.build_mailer("sendgrid", {}), m.SendgridMailer)
    assert isinstance(m.build_mailer("mailgun", {}), m.MailgunMailer)
    assert isinstance(m.build_mailer("postmark", {}), m.PostmarkMailer)
    assert isinstance(m.build_mailer("resend", {}), m.ResendMailer)
    assert isinstance(m.build_mailer("ses", {}), m.SesMailer)
    with pytest.raises(ValueError, match="unsupported"):
        m.build_mailer("nope", {})


class _Resp:
    def __init__(self, status=202, text=""):
        self.status_code, self.text = status, text


class _Client:
    def __init__(self, cap):
        self._cap = cap

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **kw):
        self._cap.append((url, kw))
        return _Resp()


@pytest.mark.asyncio
async def test_sendgrid_send_shapes_request(monkeypatch):
    cap: list = []
    monkeypatch.setattr(m.httpx, "AsyncClient", lambda *a, **k: _Client(cap))
    mailer = m.build_mailer("sendgrid", {"api_key": "SG.x", "from_email": "me@x.com"})
    res = await mailer.send(to="you@x.com", subject="Hi", html="<b>hi</b>", text="hi")
    assert res.ok
    url, kw = cap[-1]
    assert url == "https://api.sendgrid.com/v3/mail/send"
    assert kw["headers"]["Authorization"] == "Bearer SG.x"
    body = kw["json"]
    assert body["personalizations"][0]["to"][0]["email"] == "you@x.com"
    assert body["from"]["email"] == "me@x.com" and body["subject"] == "Hi"


@pytest.mark.asyncio
async def test_resend_and_mailgun_endpoints(monkeypatch):
    cap: list = []
    monkeypatch.setattr(m.httpx, "AsyncClient", lambda *a, **k: _Client(cap))
    await m.build_mailer("resend", {"api_key": "re_x", "from_email": "a@x.com"}).send(
        to="b@x.com", subject="s", text="t"
    )
    assert cap[-1][0] == "https://api.resend.com/emails"
    await m.build_mailer(
        "mailgun", {"api_key": "k", "domain": "mg.x.com", "region": "eu", "from_email": "a@x.com"}
    ).send(to="b@x.com", subject="s", text="t")
    assert cap[-1][0] == "https://api.eu.mailgun.net/v3/mg.x.com/messages"


@pytest.mark.asyncio
async def test_smtp_send(monkeypatch):
    sent: dict = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            sent["addr"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, u, p):
            sent["login"] = (u, p)

        def sendmail(self, frm, to, msg):
            sent["mail"] = (frm, to)

    monkeypatch.setattr(m.smtplib, "SMTP", FakeSMTP)
    mailer = m.build_mailer(
        "smtp",
        {
            "host": "smtp.x.com", "port": 587, "username": "u",
            "password": "p", "from_email": "me@x.com",
        },
    )
    res = await mailer.send(to="you@x.com", subject="Hi", text="hello")
    assert res.ok
    assert sent["addr"] == ("smtp.x.com", 587)
    assert sent["tls"] is True and sent["login"] == ("u", "p")
    assert sent["mail"] == ("me@x.com", ["you@x.com"])
