"""Upload safety — malware scanning + file-type validation.

Defense-in-depth before any uploaded bytes are parsed or stored:
  1. size cap
  2. true file-type check via magic bytes (never trust the client MIME)
  3. antivirus scan (ClamAV by default; pluggable via the scanner Registry)

FileScanner is the interface; ClamAVScanner / NoopScanner are adapters; ScannerRegistry
maps a key -> builder; build_file_safety() is the Factory that wires the configured
service. Adding a cloud scanner (VirusTotal, Cloudmersive, Defender) = register a builder.
"""

from __future__ import annotations

import asyncio
import io
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

# Binary types we accept for ingestion (text/markdown have no magic bytes -> allowed).
ALLOWED_BINARY_EXT: set[str] = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "tif",
    "mp4", "mov", "webm", "mkv", "avi", "m4a", "mp3", "wav",
}


class ScanError(RuntimeError):
    """Raised when scanning cannot complete and the policy is fail-closed."""


@dataclass(slots=True)
class ScanResult:
    clean: bool
    signature: str | None = None
    scanned: bool = True


@dataclass(slots=True)
class SafetyVerdict:
    ok: bool
    reason: str | None = None  # file_too_large | unsupported_type | malware_detected
    detected_type: str | None = None
    signature: str | None = None
    detail: dict = field(default_factory=dict)


class FileScanner(ABC):
    """Antivirus scanner interface."""

    name: str

    @abstractmethod
    async def scan(self, content: bytes) -> ScanResult: ...


class ClamAVScanner(FileScanner):
    name = "clamav"

    def __init__(
        self, host: str, port: int, *, fail_closed: bool = True, timeout: int = 30
    ) -> None:
        self._host = host
        self._port = port
        self._fail_closed = fail_closed
        self._timeout = timeout

    async def scan(self, content: bytes) -> ScanResult:
        import clamd  # imported lazily so the package isn't required when scanning is off

        def _do() -> dict:
            client = clamd.ClamdNetworkSocket(self._host, self._port, timeout=self._timeout)
            return client.instream(io.BytesIO(content))

        try:
            result = await asyncio.to_thread(_do)
        except Exception as exc:  # connection refused, timeout, etc.
            if self._fail_closed:
                raise ScanError(f"clamav unavailable: {exc}") from exc
            return ScanResult(clean=True, signature=None, scanned=False)

        status, signature = result.get("stream", ("OK", None))
        return ScanResult(clean=status == "OK", signature=signature, scanned=True)


class NoopScanner(FileScanner):
    """No-op scanner (scanning disabled). Size + type checks still run."""

    name = "noop"

    async def scan(self, content: bytes) -> ScanResult:
        return ScanResult(clean=True, signature=None, scanned=False)


ScannerBuilder = Callable[..., FileScanner]


class ScannerRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, ScannerBuilder] = {}

    def register(self, name: str, builder: ScannerBuilder) -> None:
        self._builders[name] = builder

    def keys(self) -> list[str]:
        return sorted(self._builders)

    def create(self, name: str, **cfg) -> FileScanner:
        builder = self._builders.get(name)
        if builder is None:
            raise ScanError(f"unknown scanner: {name}")
        return builder(**cfg)


def _default_registry() -> ScannerRegistry:
    reg = ScannerRegistry()
    reg.register(
        "clamav",
        lambda host="localhost", port=3310, fail_closed=True: ClamAVScanner(
            host, port, fail_closed=fail_closed
        ),
    )
    reg.register("noop", lambda **_: NoopScanner())
    return reg


default_scanner_registry = _default_registry()


class FileSafetyService:
    """Orchestrates size -> type -> scan and returns a single verdict."""

    def __init__(
        self,
        scanner: FileScanner,
        *,
        max_bytes: int,
        allowed_ext: set[str] | None = None,
    ) -> None:
        self._scanner = scanner
        self._max_bytes = max_bytes
        self._allowed = allowed_ext or ALLOWED_BINARY_EXT

    async def check(
        self,
        content: bytes,
        *,
        filename: str | None = None,
        declared_content_type: str | None = None,
    ) -> SafetyVerdict:
        if len(content) > self._max_bytes:
            return SafetyVerdict(
                ok=False,
                reason="file_too_large",
                detail={"size": len(content), "max": self._max_bytes},
            )

        import filetype

        kind = filetype.guess(content)
        detected = kind.extension if kind else None
        # Binary with a recognized signature must be in the allowlist; text (no magic) passes.
        if detected is not None and detected not in self._allowed:
            return SafetyVerdict(ok=False, reason="unsupported_type", detected_type=detected)

        result = await self._scanner.scan(content)
        if not result.clean:
            return SafetyVerdict(
                ok=False, reason="malware_detected", signature=result.signature
            )

        return SafetyVerdict(ok=True, detected_type=detected or "text")
