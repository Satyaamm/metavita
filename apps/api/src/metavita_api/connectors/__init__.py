"""Connector registry — default registry wired with the built-in connectors."""

from __future__ import annotations

from .base import Connector, ConnectorRegistry, FetchedDoc
from .web import WebConnector

default_connector_registry = ConnectorRegistry()
default_connector_registry.register(WebConnector())

__all__ = [
    "Connector",
    "ConnectorRegistry",
    "FetchedDoc",
    "WebConnector",
    "default_connector_registry",
]
