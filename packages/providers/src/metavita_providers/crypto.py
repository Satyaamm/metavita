"""Application-layer encryption for provider credentials.

In production the data key is wrapped by KMS/Vault; in dev we use a local Fernet
key from APP_ENCRYPTION_KEY. Provider keys are decrypted only in-process at call
time and never logged. This is the envelope referenced by the security plan.
"""

from __future__ import annotations

from cryptography.fernet import Fernet


class SecretBox:
    def __init__(self, key: str | bytes) -> None:
        if isinstance(key, str):
            key = key.encode()
        self._fernet = Fernet(key)

    @staticmethod
    def generate_key() -> str:
        """Generate a fresh urlsafe-base64 Fernet key (dev convenience)."""
        return Fernet.generate_key().decode()

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode()).decode()
