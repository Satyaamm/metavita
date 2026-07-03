"""Integration catalog primitives — the typed, data-driven registry of every
service a user can bring (LLM, embeddings, vector DB, video, rerank, storage…).

Design: an `Integration` declares its `capability`, `provider`, and the `Field`s a
user fills in to connect their own account. Secret fields are stored encrypted; the
rest are plain config. The catalog is JSON-serializable so the frontend renders the
"Add connection" form dynamically — adding a provider is one `Integration` entry,
no UI or call-site changes (registry pattern).

MetaVita ships NO platform credentials: every model/key/endpoint is brought by the
user as a Connection.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

# The capability a connection fills. Extensible — add a string + integrations.
CAPABILITIES: dict[str, str] = {
    "llm": "Language models (chat / reasoning)",
    "embeddings": "Embedding models (vectorize text)",
    "vector_store": "Vector databases (store & search embeddings)",
    "video": "Video & multimodal analyzers",
    "rerank": "Rerankers (reorder retrieved results)",
    "object_store": "Object storage (raw documents & artifacts)",
    "email": "Email delivery (send mail from your own provider)",
}

FieldType = str  # text | password | number | boolean | select


@dataclass(slots=True)
class Field:
    name: str
    label: str
    type: FieldType = "text"
    required: bool = True
    secret: bool = False  # stored encrypted, never returned to the client
    placeholder: str = ""
    help: str = ""
    options: list[str] = field(default_factory=list)  # for type == "select"
    default: str | int | bool | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "secret": self.secret,
            "placeholder": self.placeholder,
            "help": self.help,
            "options": self.options,
            "default": self.default,
        }


@dataclass(slots=True)
class TestResult:
    ok: bool
    message: str


# A tester receives the merged {**config, **secrets} dict and probes connectivity.
Tester = Callable[[dict], Awaitable[TestResult]]


@dataclass(slots=True)
class Integration:
    capability: str
    provider: str
    label: str
    description: str = ""
    docs_url: str = ""
    fields: list[Field] = field(default_factory=list)
    tester: Tester | None = None

    def secret_fields(self) -> list[str]:
        return [f.name for f in self.fields if f.secret]

    def config_fields(self) -> list[str]:
        return [f.name for f in self.fields if not f.secret]

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "provider": self.provider,
            "label": self.label,
            "description": self.description,
            "docs_url": self.docs_url,
            "fields": [f.to_dict() for f in self.fields],
        }

    async def test(self, values: dict) -> TestResult:
        if self.tester is None:
            # No live probe implemented — accept if required fields are present.
            missing = [f.name for f in self.fields if f.required and not values.get(f.name)]
            if missing:
                return TestResult(False, f"missing required fields: {', '.join(missing)}")
            return TestResult(True, "Saved. Live connectivity check not available here.")
        return await self.tester(values)


class IntegrationRegistry:
    """Holds every integration keyed by (capability, provider)."""

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], Integration] = {}

    def register(self, integration: Integration) -> Integration:
        self._by_key[(integration.capability, integration.provider)] = integration
        return integration

    def get(self, capability: str, provider: str) -> Integration | None:
        return self._by_key.get((capability, provider))

    def all(self) -> list[Integration]:
        return list(self._by_key.values())

    def catalog(self) -> dict:
        """Grouped, JSON-serializable view for the frontend."""
        groups: dict[str, list[dict]] = {cap: [] for cap in CAPABILITIES}
        for integ in self._by_key.values():
            groups.setdefault(integ.capability, []).append(integ.to_dict())
        return {
            "capabilities": [
                {"key": cap, "label": CAPABILITIES.get(cap, cap), "providers": sorted(
                    groups.get(cap, []), key=lambda d: d["label"]
                )}
                for cap in CAPABILITIES
            ]
        }
