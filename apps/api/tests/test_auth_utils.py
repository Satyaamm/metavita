"""Password + JWT utility tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from metavita_api.security.passwords import hash_password, verify_password
from metavita_api.security.tokens import TokenError, create_access_token, decode_token

SECRET = "test-secret"


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"
    assert verify_password("hunter2", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_token_roundtrip_carries_claims() -> None:
    token = create_access_token(subject="user-1", workspace_id="ws-1", secret=SECRET)
    claims = decode_token(token, secret=SECRET)
    assert claims["sub"] == "user-1"
    assert claims["ws"] == "ws-1"


def test_token_wrong_secret_rejected() -> None:
    token = create_access_token(subject="u", workspace_id="w", secret=SECRET)
    with pytest.raises(TokenError):
        decode_token(token, secret="other-secret")


def test_token_expired_rejected() -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    token = create_access_token(
        subject="u", workspace_id="w", secret=SECRET, expires_minutes=1, now=past
    )
    with pytest.raises(TokenError):
        decode_token(token, secret=SECRET)
