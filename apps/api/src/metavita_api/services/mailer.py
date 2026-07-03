"""Mailer service — send email through the workspace's own email Connection.

The platform never sends from its own account: a workspace brings an `email`
Connection (SMTP, SendGrid, Mailgun, Postmark, Resend, or Amazon SES) and we
deliver through it. `build_mailer(provider, values)` returns a Mailer whose
`send()` dispatches to the right transport.
"""

from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol

import httpx
from metavita_providers import _awssig

_TIMEOUT = 30.0


@dataclass(slots=True)
class SendResult:
    ok: bool
    detail: str


class Mailer(Protocol):
    async def send(
        self, *, to: str, subject: str, html: str | None = None, text: str | None = None
    ) -> SendResult: ...


def _from(values: dict) -> str:
    return values.get("from_email") or values.get("from") or ""


# --- SMTP (stdlib, run off the event loop) ----------------------------------
class SmtpMailer:
    def __init__(self, values: dict) -> None:
        self._host = values.get("host", "")
        self._port = int(values.get("port", 587))
        self._user = values.get("username", "")
        self._password = values.get("password", "")
        self._from = _from(values)
        self._tls = bool(values.get("use_tls", True))

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        def _send() -> SendResult:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._from
            msg["To"] = to
            if text:
                msg.attach(MIMEText(text, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            if not text and not html:
                msg.attach(MIMEText("", "plain"))
            with smtplib.SMTP(self._host, self._port, timeout=_TIMEOUT) as server:
                if self._tls:
                    server.starttls()
                if self._user:
                    server.login(self._user, self._password)
                server.sendmail(self._from, [to], msg.as_string())
            return SendResult(True, "sent via SMTP")

        try:
            return await asyncio.to_thread(_send)
        except Exception as exc:  # noqa: BLE001 - surface delivery failure
            return SendResult(False, f"SMTP error: {exc}")


# --- REST providers ----------------------------------------------------------
async def _post(url: str, *, headers=None, json=None, data=None, auth=None) -> SendResult:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=json, data=data, auth=auth)
        if resp.status_code < 300:
            return SendResult(True, f"accepted (HTTP {resp.status_code})")
        return SendResult(False, f"HTTP {resp.status_code}: {resp.text[:200]}")
    except httpx.HTTPError as exc:
        return SendResult(False, f"unreachable: {exc.__class__.__name__}")


class SendgridMailer:
    def __init__(self, values: dict) -> None:
        self._key = values.get("api_key", "")
        self._from = _from(values)

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        content = [{"type": "text/plain", "value": text or ""}]
        if html:
            content.append({"type": "text/html", "value": html})
        return await _post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": self._from},
                "subject": subject,
                "content": content,
            },
        )


class MailgunMailer:
    def __init__(self, values: dict) -> None:
        self._key = values.get("api_key", "")
        self._domain = values.get("domain", "")
        self._from = _from(values)
        host = "api.eu.mailgun.net" if values.get("region") == "eu" else "api.mailgun.net"
        self._url = f"https://{host}/v3/{self._domain}/messages"

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        data = {"from": self._from, "to": to, "subject": subject}
        if text:
            data["text"] = text
        if html:
            data["html"] = html
        return await _post(self._url, data=data, auth=("api", self._key))


class PostmarkMailer:
    def __init__(self, values: dict) -> None:
        self._token = values.get("server_token", "")
        self._from = _from(values)

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        body = {"From": self._from, "To": to, "Subject": subject}
        if html:
            body["HtmlBody"] = html
        if text:
            body["TextBody"] = text
        return await _post(
            "https://api.postmarkapp.com/email",
            headers={"X-Postmark-Server-Token": self._token, "Accept": "application/json"},
            json=body,
        )


class ResendMailer:
    def __init__(self, values: dict) -> None:
        self._key = values.get("api_key", "")
        self._from = _from(values)

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        body = {"from": self._from, "to": [to], "subject": subject}
        if html:
            body["html"] = html
        if text:
            body["text"] = text
        return await _post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {self._key}"},
            json=body,
        )


class SesMailer:
    def __init__(self, values: dict) -> None:
        self._region = values.get("region", "us-east-1")
        self._access = values.get("access_key_id", "")
        self._secret = values.get("secret_access_key", "")
        self._from = _from(values)
        self._host = f"email.{self._region}.amazonaws.com"

    async def send(self, *, to, subject, html=None, text=None) -> SendResult:
        import json as _json

        body_content: dict = {}
        if html:
            body_content["Html"] = {"Data": html}
        if text or not html:
            body_content["Text"] = {"Data": text or ""}
        payload = _json.dumps({
            "FromEmailAddress": self._from,
            "Destination": {"ToAddresses": [to]},
            "Content": {"Simple": {"Subject": {"Data": subject}, "Body": body_content}},
        }).encode()
        path = "/v2/email/outbound-emails"
        headers = _awssig.sigv4_headers(
            method="POST", host=self._host, path=path, region=self._region,
            service="ses", payload=payload, access_key=self._access, secret_key=self._secret,
        )
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"https://{self._host}{path}", headers=headers, content=payload
                )
            if resp.status_code < 300:
                return SendResult(True, f"accepted (HTTP {resp.status_code})")
            return SendResult(False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.HTTPError as exc:
            return SendResult(False, f"unreachable: {exc.__class__.__name__}")


_BUILDERS = {
    "smtp": SmtpMailer,
    "sendgrid": SendgridMailer,
    "mailgun": MailgunMailer,
    "postmark": PostmarkMailer,
    "resend": ResendMailer,
    "ses": SesMailer,
}


def build_mailer(provider: str, values: dict) -> Mailer:
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ValueError(f"unsupported email provider: {provider}")
    return builder(values)
