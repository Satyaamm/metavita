"""Application settings, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://metavita:metavita@localhost:5432/metavita"
    redis_url: str = "redis://localhost:6379/0"

    # Object store
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "metavita"
    s3_region: str = "us-east-1"
    local_object_root: str = "/tmp/metavita-objects"  # LocalObjectStore fallback root

    # Security
    app_encryption_key: str = ""  # dev: Fernet key; prod: KMS-wrapped
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"

    # Upload safety. Size cap always applies. Malware scanning is OPTIONAL and OFF
    # by default (there's no pure-Python AV — it needs a ClamAV daemon); operators
    # opt in by running ClamAV and setting enable_file_scanning=true.
    enable_file_scanning: bool = False
    scan_provider: str = "clamav"
    clamav_host: str = "localhost"
    clamav_port: int = 3310
    max_upload_mb: int = 32

    # Models & services are NOT configured here — they are brought by each workspace
    # as encrypted Connections (LLM / embeddings / vector DB / video / email / …).
    # The platform holds no provider keys and no default provider/model/dimension.

    # CORS for the local web app
    cors_origins: list[str] = ["http://localhost:3000"]
    # Public base URL of the web app — used to build invite/accept links in emails.
    app_base_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
