# MetaVita — Architecture

MetaVita is an open-core, **bring-your-own-everything** agentic RAG platform: users connect
their own model and data services, build RAG-powered agents and pipelines through a hybrid
**visual builder + code escape-hatch**, and deploy them as APIs and embeddable widgets. It is
provider-agnostic, self-hostable, and built with **GDPR / SOC 2 / HIPAA** controls in mind.

## Bring-your-own, no fallback

The platform holds **no provider credentials of its own**. Every capability is supplied by a
workspace **Connection**, and resolution has no fallback: `ProviderFactory`
(`apps/api/src/metavita_api/factory.py`) reads the workspace's default Connection for a
capability and raises `HTTP 400` if none exists. There is no platform-managed key mode and no
environment-variable fallback.

Capabilities (see `apps/api/src/metavita_api/integrations/catalog.py`):

| Capability | Example providers |
|---|---|
| `llm` | Anthropic, OpenAI, Azure OpenAI, Bedrock, Vertex, Mistral, Groq, Together, OpenRouter, Ollama, OpenAI-compatible |
| `embeddings` | OpenAI, Azure OpenAI, Cohere, Voyage, Jina, Ollama |
| `vector_store` | pgvector (built-in), Pinecone, Qdrant, Weaviate, Chroma, Milvus, Moss |
| `video` | Azure AI Vision, AWS Rekognition Video, Google Video Intelligence, TwelveLabs |
| `rerank` | Cohere, Jina, Voyage |
| `object_store` | MinIO, S3, GCS, Azure Blob |
| `email` | SMTP, SendGrid, Mailgun, Postmark, Resend, SES |

Connection secrets are envelope-encrypted with a Fernet `SecretBox`
(`security/encryption.py`) before storage.

## Components

| Component | Path | Role |
|---|---|---|
| Web app | `apps/web` | Next.js 15 + Fluent UI v9. Login-gated SPA: knowledge, visual/code builder, playground, deployments, observe, connections, settings. |
| API gateway | `apps/api` | FastAPI. Auth/RBAC, connections, ingest/query, build, serving, compliance, audit. |
| Workers | `apps/worker` | Arq workers for ingestion and execution. |
| Runtime engine | `packages/runtime` | Parse → chunk → embed (ingest); retrieve → LLM answer with citations. Storage-agnostic via the `VectorStore` port. |
| Provider layer | `packages/providers` | Adapters implementing a unified chat/embedding interface per provider. |
| Data | Postgres + pgvector, Redis, MinIO/S3 | Metadata + vectors, queue/cache, raw objects. |

## Data path

```
upload ──▶ apps/api /ingest ──▶ runtime.ingest_document
                                 parse → chunk → embed (workspace `embeddings` Connection)
                                 ──▶ chunks + vectors stored via the resolved vector store

ask ─────▶ apps/api /query/stream ──▶ runtime.stream_answer
                                 embed question (same embeddings Connection)
                                 → vector search (workspace `vector_store`, pgvector by default)
                                 → prompt with numbered context
                                 → workspace `llm` Connection streams a cited answer (SSE)
```

The chat and embedding providers/models are whatever the workspace connected — nothing is
hardcoded. Video ingestion embeds a whole-video vector through the workspace's `video`
Connection (with a basic offline fallback when none is connected).

## Vector storage

The vector store is a port (`vectorstores/factory.py`) with pgvector as the built-in default
plus external adapters (Pinecone, Qdrant, Weaviate, Chroma, Moss). The built-in pgvector
`chunks.embedding` column is **dimensionless**: the workspace's embedding model decides the
vector dimension at write time (migration `0013_dimensionless_vectors`). Because a fixed-dimension
ANN index requires a fixed dimension, the previous HNSW index was dropped and search uses exact
cosine distance; an operator can add an ANN index once a dimension is fixed. External vector
databases have no such constraint.

## Auth, RBAC & invitations

- **Auth:** JWT signup/login/`me` plus forgot/reset password (`routes/auth.py`). The web app is
  login-gated (`apps/web/components/AppShell.tsx`); public routes are `/login`, `/signup`,
  `/forgot`, `/reset`, and `/invite`.
- **RBAC:** ranked roles (viewer < editor < admin < owner) enforced by `deps.require_role`
  on management endpoints.
- **Invitations:** invite-by-URL (`routes/invites.py`). Invitations and password-reset links are
  delivered through the workspace's own `email` Connection — you cannot invite a member without a
  connected email provider. Accepting an invite creates the user + membership and returns a session.

## Security & compliance

- **Tenant isolation:** every row carries `workspace_id`; Postgres RLS policies are created in the
  migrations as defense-in-depth alongside app-layer scoping.
- **Audit:** append-only, hash-chained `audit_logs` for tamper-evident evidence.
- **Secrets:** Connection credentials envelope-encrypted with a Fernet key; supply a KMS-managed
  `APP_ENCRYPTION_KEY` in production.
- **BAA gating:** HIPAA workspaces restrict providers to an `allowed_providers` allow-list,
  enforced at provider construction.
- **Upload safety:** uploads are size-capped; optional ClamAV malware scanning is **off by
  default** and enabled per deployment (there is no pure-Python antivirus).
- **DSAR:** data-subject export and erasure with retention enforcement (`routes/compliance.py`).

## Deployment

Container images for the API and worker, a production compose file
(`infra/docker/docker-compose.prod.yml`), and a Helm chart (`infra/helm/metavita`) are provided.
Local development is orchestrated by `run.sh` (Docker infra + venv + migrations + dev servers).

See [`remaining-roadmap.md`](remaining-roadmap.md) for what is shipped and what is planned.
