# MetaVita

> A **bring-your-own-everything** agentic RAG platform. Connect your own models and
> data services, build RAG-powered agents and pipelines with a hybrid **visual builder
> + code escape-hatch**, and deploy them as APIs and embeddable widgets.

MetaVita is **open-core**: architected SaaS-first but fully self-hostable, and
**provider-agnostic by design**. The platform ships with **no provider keys of its own** —
every workspace brings its own LLM, embeddings, vector store, video, rerank, object-store,
and email services as encrypted **Connections**. It is built with GDPR / SOC 2 / HIPAA
controls in mind (per-workspace isolation via Postgres RLS, encrypted secrets, an immutable
hash-chained audit log, and DSAR export/erasure).

## Bring-your-own model

There are no platform-managed credentials and no built-in defaults. A feature that needs a
capability resolves it **only** from the workspace's Connection for that capability; if none
is configured, the API returns a clear `400` directing the user to add one. Consequences of
this design:

- **No provider keys in the environment.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and any
  default provider/model settings are intentionally absent — you add providers in the app's
  **Connections** page, encrypted per workspace.
- **The embedding dimension is decided by your model.** The built-in pgvector store uses a
  dimensionless vector column, so whatever dimension your embedding model produces is what's
  stored. (An operator can add an ANN index once a fixed dimension is chosen; bring-your-own
  vector databases have no such constraint.)
- **All system email is bring-your-own too.** Invitations and password-reset links are sent
  through the workspace's own email Connection — you cannot invite a member without first
  connecting an email provider.

## Capabilities

- **Knowledge** — upload documents (PDF/DOCX/Markdown/HTML), crawl web pages, and ingest
  video; parse → chunk → embed → store, with a chunk inspector.
- **Pluggable vector stores** — pgvector (built-in) plus Pinecone, Qdrant, Weaviate, Chroma,
  and Moss, selected per workspace.
- **Build** — a visual pipeline/DAG builder and an agent builder (ReAct tool loop), with a
  per-node connection slot for each capability (LLM / embeddings / retrieve / video).
- **Playground** — chat against a pipeline, agent, or your knowledge base with retrieved
  context shown alongside and inline citations.
- **Deploy** — publish pipelines/agents as HTTP endpoints and an embeddable chat `widget.js`;
  thin TypeScript and Python SDKs.
- **Observe** — traces, analytics, and an immutable audit log.
- **Governance** — auth (JWT), role-based access control, workspace invitations, and
  compliance tooling (DSAR export/erasure, retention, BAA provider gating).
- **Tools & Prompts** — a tool registry and a versioned prompt library.

## Monorepo layout

```
apps/
  web/          Next.js 15 + Fluent UI v9 frontend
  api/          FastAPI gateway
  worker/       Arq ingestion + execution workers
packages/
  runtime/      DAG executor + agent loop (core engine, Python)
  providers/    LLM / embeddings / rerank provider adapters (Python)
  schemas/      Shared pipeline-graph JSON schema
  sdk-ts/       TypeScript SDK
  sdk-py/       Python SDK
  ui/           Shared React components
infra/
  docker/       docker-compose for local infra + production compose
  helm/         Helm chart for Kubernetes
```

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15, TypeScript, Fluent UI v9 (Griffel), xyflow, Monaco, Zustand |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Data | Postgres 16 + pgvector, Redis 7, MinIO / S3 |
| Workers | Arq |

## Quick start (local dev)

The `run.sh` script brings up the Docker infra (Postgres + pgvector, Redis, MinIO), creates a
Python virtualenv, applies migrations, and starts the API, worker, and web dev server:

```bash
./run.sh
```

Then open **http://localhost:3000**, create an account, and — because MetaVita is
bring-your-own — open **Connections** to add at least an **LLM** and an **embedding** provider
(with your own keys) before ingesting documents or running queries.

Useful flags:

```bash
./run.sh --down       # stop the app processes and the Docker infra
./run.sh --rebuild    # force-reinstall the Python venv and web deps
./run.sh --no-web     # API + worker only (skip the Next.js dev server)
./run.sh --scan       # also start ClamAV and enable upload malware scanning
```

Prefer to run things by hand? Install the backend into a virtualenv
(`python -m venv .venv && .venv/bin/pip install -e packages/providers -e packages/runtime -e apps/api`),
run `.venv/bin/alembic -c apps/api/alembic.ini upgrade head`, start
`.venv/bin/uvicorn metavita_api.main:app --reload`, and in `apps/web` run `npm install && npm run dev`.

## Configuration

Copy `.env.example` to `.env`. The environment holds **only infrastructure and security**
settings — database, Redis, object store, the app encryption key, and the JWT secret. There
are no model or provider settings; those live in **Connections**. Notable values:

| Variable | Purpose |
|---|---|
| `DATABASE_URL`, `REDIS_URL` | Postgres (pgvector) and Redis |
| `S3_*` | Object store (MinIO in dev, S3 in prod) |
| `APP_ENCRYPTION_KEY` | Fernet key used to encrypt Connection secrets (set a real key in production) |
| `JWT_SECRET` | Signing secret for auth tokens (rotate off the default in production) |
| `APP_BASE_URL` | Public web URL used to build invite / password-reset links in emails |
| `ENABLE_FILE_SCANNING` | Optional ClamAV upload scanning — **off by default** |

Upload malware scanning is optional and disabled by default; enabling it requires a running
ClamAV daemon (there is no pure-Python antivirus).

## Self-hosting

Container images are provided for the API and worker (`apps/api/Dockerfile`,
`apps/worker/Dockerfile`), a production compose file (`infra/docker/docker-compose.prod.yml`),
and a Helm chart (`infra/helm/metavita`). For production, supply a KMS-managed
`APP_ENCRYPTION_KEY` and `JWT_SECRET`, and point `S3_*` at your object store.

## Status

The v1 platform is implemented end-to-end: bring-your-own connections, pluggable vector
stores, the visual/code builder, agents and pipelines, playground, deployments and SDKs,
observability, auth/RBAC/invitations, and compliance tooling.

External provider adapters (cloud LLMs, managed vector databases, video, and email providers)
are covered by unit tests with mocked transports; validate them against live accounts with
`scripts/byo_e2e.py`. Hierarchical (RAPTOR-style) indexing, OAuth/SSO sign-in, and billing are
planned for a future release.

## License

Open-core. License TBD.
