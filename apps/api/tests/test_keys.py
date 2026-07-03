"""API key generation/verification tests."""

from __future__ import annotations

from metavita_api.security.keys import generate_api_key, hash_key, verify_key


def test_generate_returns_prefixed_key_and_matching_hash() -> None:
    key, prefix, hashed = generate_api_key()
    assert key.startswith("mv_")
    assert prefix == key[:11]
    assert hashed == hash_key(key)
    assert hashed != key  # hash, not the secret


def test_verify_accepts_correct_and_rejects_wrong() -> None:
    key, _prefix, hashed = generate_api_key()
    assert verify_key(key, hashed) is True
    assert verify_key("mv_wrongkey", hashed) is False


def test_keys_are_unique() -> None:
    a, _, _ = generate_api_key()
    b, _, _ = generate_api_key()
    assert a != b
