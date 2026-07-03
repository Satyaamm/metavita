"""JWT access tokens — pure encode/decode (testable with an injected secret)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt


class TokenError(Exception):
    pass


def create_access_token(
    *,
    subject: str,
    workspace_id: str,
    secret: str,
    algorithm: str = "HS256",
    expires_minutes: int = 60 * 24 * 7,
    now: datetime | None = None,
) -> str:
    issued = now or datetime.now(UTC)
    payload = {
        "sub": subject,
        "ws": workspace_id,
        "iat": int(issued.timestamp()),
        "exp": int((issued + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str = "HS256") -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
