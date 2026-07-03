"""Factory: build a configured FileSafetyService from settings."""

from __future__ import annotations

from ..config import Settings
from .scanning import FileSafetyService, NoopScanner, default_scanner_registry


def build_file_safety(settings: Settings) -> FileSafetyService:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if not settings.enable_file_scanning:
        return FileSafetyService(NoopScanner(), max_bytes=max_bytes)

    scanner = default_scanner_registry.create(
        settings.scan_provider,
        host=settings.clamav_host,
        port=settings.clamav_port,
        # Dev fails open (clamav may be absent); other envs fail closed.
        fail_closed=settings.environment != "development",
    )
    return FileSafetyService(scanner, max_bytes=max_bytes)
