"""Integration catalog tests — registry shape, serialization, secret partitioning."""

from __future__ import annotations

import pytest
from metavita_api.integrations import default_integration_registry as catalog
from metavita_api.integrations.base import CAPABILITIES


def test_catalog_covers_every_capability_with_providers():
    cat = catalog.catalog()
    caps = {c["key"] for c in cat["capabilities"]}
    assert caps == set(CAPABILITIES)
    for cap in cat["capabilities"]:
        assert cap["providers"], f"no providers for {cap['key']}"


def test_catalog_is_json_serializable_and_marks_secrets():
    import json

    cat = catalog.catalog()
    json.dumps(cat)  # must not raise
    openai = next(
        p for c in cat["capabilities"] if c["key"] == "llm"
        for p in c["providers"] if p["provider"] == "openai"
    )
    api_key = next(f for f in openai["fields"] if f["name"] == "api_key")
    assert api_key["secret"] is True and api_key["type"] == "password"


def test_byo_providers_present_for_key_vendors():
    providers = {(i.capability, i.provider) for i in catalog.all()}
    for expected in [
        ("llm", "openai"), ("llm", "anthropic"), ("llm", "aws_bedrock"), ("llm", "gcp_vertex"),
        ("embeddings", "openai"), ("embeddings", "cohere"),
        ("vector_store", "pinecone"), ("vector_store", "qdrant"), ("vector_store", "weaviate"),
        ("vector_store", "chroma"), ("vector_store", "pgvector"),
        ("video", "azure_video"), ("object_store", "s3"),
    ]:
        assert expected in providers, f"missing integration {expected}"


def test_secret_fields_partition():
    integ = catalog.get("vector_store", "qdrant")
    assert "api_key" in integ.secret_fields()
    assert "url" in integ.config_fields()


@pytest.mark.asyncio
async def test_test_without_required_fields_reports_missing():
    integ = catalog.get("llm", "openai")
    result = await integ.test({})  # no api_key
    assert result.ok is False and "api_key" in result.message
