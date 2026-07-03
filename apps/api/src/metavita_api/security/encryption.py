"""Workspace secret encryption — wraps the provider SecretBox.

Uses APP_ENCRYPTION_KEY (KMS-wrapped in prod). In dev, if unset, derives a stable
key from a fixed seed so encrypted values survive restarts — NOT for production.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from metavita_providers import SecretBox

from ..config import get_settings


@lru_cache
def get_secret_box() -> SecretBox:
    key = get_settings().app_encryption_key
    if not key:
        key = base64.urlsafe_b64encode(hashlib.sha256(b"metavita-dev-key").digest()).decode()
    return SecretBox(key)
