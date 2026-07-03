"""Connector abstraction — pluggable adapters that fetch documents from a source.

A connector yields `FetchedDoc`s (raw bytes + metadata); the caller ingests them
through the normal parse→chunk→embed→store path. Connectors are registered in a
`ConnectorRegistry` (registry pattern), keyed by name, and discovered by the API.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class FetchedDoc:
    filename: str
    content: bytes
    content_type: str | None = None
    meta: dict = field(default_factory=dict)


class Connector(Protocol):
    """Fetches documents from an external source described by `config`."""

    name: str

    def fetch(self, config: dict) -> AsyncIterator[FetchedDoc]: ...


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> Connector:
        self._connectors[connector.name] = connector
        return connector

    def get(self, name: str) -> Connector:
        if name not in self._connectors:
            raise KeyError(f"unknown connector '{name}' (have: {sorted(self._connectors)})")
        return self._connectors[name]

    def names(self) -> list[str]:
        return sorted(self._connectors)
