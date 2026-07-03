"""Upload-safety tests — size cap, magic-byte type check, malware scan (faked AV)."""

from __future__ import annotations

import pytest
from metavita_api.security.scanning import (
    FileSafetyService,
    FileScanner,
    NoopScanner,
    ScanResult,
    default_scanner_registry,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
ZIP = b"PK\x03\x04" + b"\x00" * 64
TEXT = b"the quick brown fox jumps over the lazy dog"
EICAR_ISH = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE"


class FakeInfectedScanner(FileScanner):
    """Flags any payload containing the EICAR marker."""

    name = "fake"

    async def scan(self, content: bytes) -> ScanResult:
        if b"EICAR" in content:
            return ScanResult(clean=False, signature="Eicar-Test-Signature")
        return ScanResult(clean=True)


def _svc(scanner: FileScanner, max_bytes: int = 32 * 1024 * 1024) -> FileSafetyService:
    return FileSafetyService(scanner, max_bytes=max_bytes)


@pytest.mark.asyncio
async def test_clean_text_passes() -> None:
    v = await _svc(NoopScanner()).check(TEXT, filename="a.txt")
    assert v.ok and v.detected_type == "text"


@pytest.mark.asyncio
async def test_allowed_binary_png_passes() -> None:
    v = await _svc(NoopScanner()).check(PNG, filename="a.png")
    assert v.ok and v.detected_type == "png"


@pytest.mark.asyncio
async def test_oversized_rejected() -> None:
    v = await _svc(NoopScanner(), max_bytes=16).check(TEXT)
    assert not v.ok and v.reason == "file_too_large"


@pytest.mark.asyncio
async def test_unsupported_type_rejected() -> None:
    v = await _svc(NoopScanner()).check(ZIP, filename="a.zip")
    assert not v.ok and v.reason == "unsupported_type" and v.detected_type == "zip"


@pytest.mark.asyncio
async def test_malware_rejected() -> None:
    v = await _svc(FakeInfectedScanner()).check(EICAR_ISH, filename="x.txt")
    assert not v.ok and v.reason == "malware_detected"
    assert v.signature == "Eicar-Test-Signature"


def test_registry_and_factory() -> None:
    assert set(default_scanner_registry.keys()) == {"clamav", "noop"}
    assert isinstance(default_scanner_registry.create("noop"), NoopScanner)
