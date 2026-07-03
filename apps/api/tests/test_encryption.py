"""Workspace secret encryption tests."""

from __future__ import annotations

from metavita_api.security.encryption import get_secret_box


def test_encrypt_decrypt_roundtrip() -> None:
    box = get_secret_box()
    token = box.encrypt("sk-secret-123")
    assert token != "sk-secret-123"
    assert box.decrypt(token) == "sk-secret-123"


def test_ciphertext_is_nondeterministic() -> None:
    box = get_secret_box()
    assert box.encrypt("same") != box.encrypt("same")  # Fernet adds IV/timestamp
