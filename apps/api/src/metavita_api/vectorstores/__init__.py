"""Pluggable vector stores — Port (upsert + search) and a factory over providers.

The default store is pgvector (the platform DB). A workspace can bring its own
vector DB as a `vector_store` Connection; the factory builds the matching adapter.
External adapters (Pinecone / Qdrant / Weaviate / Chroma) register here as they land;
until then the factory falls back to pgvector so retrieval always works.
"""

from __future__ import annotations

from .factory import build_vector_store, resolve_vector_store
from .pgvector import PgVectorStore

__all__ = ["PgVectorStore", "build_vector_store", "resolve_vector_store"]
