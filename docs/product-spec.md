# MetaVita — Product Spec

The product vision and feature surface, and how each part works. Scope: build **all core
domains to full, polished feature-completeness**, **visual-first for non-technical users**,
with a code escape-hatch underneath.

> This document describes the product design. For the current shipped-vs-planned status,
> see [`remaining-roadmap.md`](remaining-roadmap.md). Where implementation differs from an
> early design note, the code and the roadmap are authoritative.

## 1. Primary user & principles

- **Primary persona:** non-technical builder. Lead with **visual builders + wizards**; never require code. A **code/JSON escape-hatch** sits under every visual surface for power users.
- **Bar:** every screen ships real (working FastAPI backend) **and** polished (refined Fluent UI) before it's "done."
- **UX principles:** guided **wizards** for first-run, meaningful **empty states** with one primary CTA, a global **⌘K command palette**, inline **notifications** (bell), optimistic feedback, and consistent card/list/detail patterns.
- **Engineering conventions:** FastAPI + SQLAlchemy/Alembic; Factory/Registry/OOP on back and front. New pluggable things (connectors, node types, tools) = interface + registry + factory.

## 2. Information architecture (navigation)

```
Overview     → Dashboard
Knowledge    → Data Sources · Documents · Indexes
Build        → Pipelines · Agents · Tools · Prompts
Test         → Playground · Evals
Ship         → Deployments · API Keys
Observe      → Traces · Analytics · Audit log
Settings     → Workspace · Members & Roles · Connections · Security & Compliance · Billing
```

Each top item is a Next.js route; the sidebar drives routing (active = current route).

## 3. Domains

### 3.1 Knowledge
**Goal:** get data in and make it retrievable — with zero code.
- **Data Sources:** wizard to add a source — Upload (done), Web URL/crawl, Connectors (Google Drive, Notion, S3, Confluence, Postgres). Connectors sync on a schedule; status chips (syncing/indexed/error).
- **Documents:** searchable list with status; **chunk inspector** detail — shows how a doc was split, each chunk's text + score on test queries (debugging retrieval visually).
- **Indexes (Collections):** group sources into a retrievable index; pick embedding model + chunk size/overlap via a form (no code). Retrieval/pipelines target an index.
- **Backend:** `data_sources`, `documents`, `chunks` (have) + `indexes`, `connector_runs`. Connectors are Registry-registered adapter classes. Workers (Arq) run syncs.

### 3.2 Pipelines (visual RAG builder) — flagship
**Goal:** assemble a retrieval flow by dragging nodes.
- **Canvas (xyflow):** node palette → Source · Chunk · Embed · Retrieve (vector / hybrid / rerank) · LLM · Router · Filter · Tool · Output. Connect, configure each via a side panel form.
- **Code view (Monaco):** same graph as JSON; round-trip safe (the visual/code parity contract).
- **Run drawer:** execute with a sample input; stream the trace inline. **Publish** → Deployment.
- **Backend:** `pipelines` (versioned graph JSON) + the runtime DAG executor; node types via a **node registry**.

### 3.3 Agents
**Goal:** wrap retrieval in an agent, visually.
- **Builder:** form/visual config — system prompt (with Prompt library), model picker (provider-routed), **tools** (retriever-as-tool, HTTP, code-exec, MCP) toggled on, **memory** on/off, attached indexes/pipelines.
- **Tools registry:** manage custom + MCP tools agents can use.
- **Backend:** `agents`, ReAct loop in runtime, spans per step.

### 3.4 Playground (Test)
**Goal:** try a pipeline/agent before shipping.
- Chat UI (seed exists) + **retrieval inspector** side panel (chunks, scores, citations), model/effort switcher, **side-by-side compare** of two configs.
- **Evals:** upload a Q/A dataset, run through a pipeline, score faithfulness/relevance/cost; results table.

### 3.5 Deployments (Ship)
**Goal:** publish with one click.
- Publish an agent/pipeline → versioned **REST endpoint** + scoped **API key** + **embeddable chat widget** (`<script>` snippet) + hosted **share page**. Version pin + rollback.
- **Backend:** `deployments`, `api_keys`; a serving route that runs the pinned version.

### 3.6 Observe
- **Traces:** span tree per run (token/cost/latency, retrieved context) — from `runs`/`spans`.
- **Analytics:** volume/latency/cost dashboards, top documents.
- **Audit log:** hash-chained events (have).

### 3.7 Settings & governance
- **Workspace**, **Members & Roles** (RBAC), **Connections** (bring-your-own providers per capability — LLM, embeddings, vector store, video, rerank, object store, email — encrypted via `SecretBox`; no platform keys, no fallback), **Security & Compliance** (data residency, retention, DSAR export/erasure, HIPAA BAA gating), **Billing/Usage**.

### 3.8 Modalities & embedders (multimodal, incl. video)
**Goal:** support text, image, audio, and **video** — with provider-specific, user-supplied models.
- **Modality-aware embedder registry/factory** (extends the provider Registry): register embedders per modality. Video providers include **Azure AI Vision**, **AWS Rekognition Video**, **Google Video Intelligence**, and **TwelveLabs** — all bring-your-own (a basic offline fallback is used when no video Connection is set).
- **Data sources carry a `modality`**; a **video** source runs a video pipeline: **ASR transcription** + **frame sampling** → embed with the selected video embedder → store **time-coded** segment vectors in pgvector (segment start/end in chunk metadata).
- **Retrieval** returns time-coded segments; playground/citations deep-link to the moment (`?t=` on the video). Indexes pin a modality + embedder; the embedding model determines the vector dimension (the built-in pgvector store is dimensionless).
- **Connections** let users add provider configs per capability (e.g., Azure endpoint + deployment + key), encrypted via `SecretBox`.
- **Backend:** new `VideoEmbeddingProvider`/multimodal interface + Azure adapter, registered in the embedder registry; modality on `data_sources`/`indexes`; ASR + frame workers (Arq).

### 3.9 Upload safety
**Goal:** uploads are size-capped and type-checked; optional antivirus scanning is available for deployments that need it.
- **Size cap** always applies (`MAX_UPLOAD_MB`).
- **Malware scanning is optional and off by default.** There is no pure-Python antivirus, so scanning requires a **ClamAV** daemon (via a `FileScanner` interface + `clamd` client). Operators opt in by running ClamAV and setting `ENABLE_FILE_SCANNING=true` (e.g., `run.sh --scan`). The registry is extensible to cloud AV adapters.
- **Pipeline (when enabled):** on every upload/connector fetch → (1) size cap, (2) file-type check, (3) AV scan → reject + audit-log on hit. Uploads are stored raw in object storage and parsed in a worker; uploads are never executed.
- **Backend:** `FileScanner` adapters in a registry; a scan hook in the ingest route + connector workers; detections recorded in `audit_logs`.

## 4. Cross-cutting
- **Auth & multi-tenancy:** JWT + workspaces + RBAC + invitations; the app is login-gated and every screen is workspace-scoped.
- **⌘K command palette**, **notifications**, **onboarding wizard** (connect → build → deploy), **empty states**, **profile/avatar menu** (have).

## 5. Data model additions (beyond M0)
`organizations`, `memberships`, `indexes`, `connector_runs`, `pipelines`, `agents`, `tools`, `prompts`, `deployments`, `api_keys`, `runs`, `spans`, `eval_datasets`, `eval_runs`, plus GDPR `consents`/`dsar` (have stubs).

## 6. Build sequence (each phase = real + polished)
1. **Foundation:** routing for all sections, app-shell polish, auth/workspaces/members (M1).
2. **Knowledge:** sources + connectors, documents, chunk inspector, indexes.
3. **Pipelines:** visual builder + code view + run trace.
4. **Agents + Tools:** builder, tool registry, agent loop.
5. **Playground + Evals:** test surface, retrieval inspector, datasets.
6. **Deployments:** API + widget + versioning.
7. **Observe + Settings:** traces UI, analytics, governance.

Dependency order is why Knowledge precedes Pipelines precedes Agents; all are in scope at full polish.
