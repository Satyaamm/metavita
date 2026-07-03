"""Integration catalog — the registry of every bring-your-own service."""

from __future__ import annotations

from .base import (
    CAPABILITIES,
    Field,
    Integration,
    IntegrationRegistry,
    TestResult,
)
from .catalog import default_integration_registry

__all__ = [
    "CAPABILITIES",
    "Field",
    "Integration",
    "IntegrationRegistry",
    "TestResult",
    "default_integration_registry",
]
