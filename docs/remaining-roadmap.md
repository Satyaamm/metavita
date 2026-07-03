# MetaVita — Roadmap

This document tracks what is shipped in v1 and what is planned for later releases.

## Shipped (v1)

**Bring-your-own foundation**
- Connections framework: encrypted, per-workspace providers across `llm`, `embeddings`,
  `vector_store`, `video`, `rerank`, `object_store`, and `email` capabilities, driven by a
  data-defined catalog.
- Pure BYO resolution with no fallback — the platform holds no provider keys; missing
  capabilities return a clear `HTTP 400`.
- Pluggable vector stores: pgvector (built-in) plus Pinecone, Qdrant, Weaviate, Chroma, and Moss.
- Dimensionless pgvector column — the embedding model decides the vector dimension.

**Knowledge & ingestion**
- Document upload (PDF/DOCX/Markdown/HTML) with parse → chunk → embed → store and a chunk inspector.
- Web crawl and connector registry.
- Video ingestion through a workspace `video` Connection.
- Asynchronous ingestion via Arq workers with object storage (MinIO/S3).

**Build, test & ship**
- Visual pipeline/DAG builder and a true DAG executor.
- Agent builder with a ReAct tool loop and a tool registry.
- Versioned prompt library.
- Per-node connection slots (LLM / embeddings / retrieve / video).
- Playground with retrieved-context inspector and citations.
- Deployments as HTTP endpoints and an embeddable `widget.js`.
- TypeScript and Python SDKs.

**Govern & observe**
- Auth (JWT signup/login/me, forgot/reset password) with a login-gated web app.
- Role-based access control (viewer / editor / admin / owner).
- Workspace invitations by token URL, delivered through the workspace's own email Connection.
- Traces, analytics, and an immutable hash-chained audit log.
- Compliance: DSAR export/erasure, retention enforcement, and BAA provider gating.

**Operations**
- Container images for API and worker, a production compose file, and a Helm chart.
- GitHub Actions CI (lint, test, build) and a database-integration test suite.
- `run.sh` for local development (infra + venv + migrations + dev servers).

## Planned (v2)

- **Hierarchical (RAPTOR-style) indexing** — an optional per-index strategy that clusters
  chunks, summarizes them with the workspace's own LLM, and builds a tree of summary nodes for
  collapsed-tree retrieval. Additive; the flat strategy remains the default.
- **OAuth / SSO sign-in** — social and enterprise single sign-on alongside email/password.
- **Billing & metering** — usage metering, plans, and a billing surface.

## Conventions

FastAPI + SQLAlchemy/Alembic on the backend; Next.js + Fluent UI v9 + Zustand on the frontend.
Factory/Registry patterns, tests alongside implementation, and no placeholder data.
