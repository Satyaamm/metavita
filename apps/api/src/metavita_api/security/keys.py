"""API key generation + verification (pure, testable).

Keys are shown to the user exactly once at creation; we store only a sha256 hash
and a short non-secret prefix (for display/identification). Verification is
constant-time.
"""

from __future__ import annotations

import hashlib
import secrets

KEY_PREFIX = "mv_"


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, display_prefix, sha256_hash). Persist only prefix + hash."""
    key = f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"
    return key, key[: len(KEY_PREFIX) + 8], hash_key(key)


def verify_key(key: str, hashed: str) -> bool:
    return secrets.compare_digest(hash_key(key), hashed)
