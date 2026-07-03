# @metavita/sdk

Official TypeScript SDK for the [MetaVita](../../README.md) agentic RAG platform — a thin, typed wrapper over the REST API. Runs in the browser, Node 18+, and edge runtimes.

## Install

```bash
npm install @metavita/sdk
```

## Usage

```ts
import { MetaVita } from "@metavita/sdk";

// Public serving surface — authenticate with a deployment key.
const mv = new MetaVita({ baseUrl: "https://api.metavita.dev", apiKey: "mv_..." });
const res = await mv.serve(deploymentId, { question: "What changed in v2?" });
console.log(res.answer, res.citations);

// Authenticated builder API — authenticate with a workspace JWT.
const mvAuth = new MetaVita({ baseUrl: "https://api.metavita.dev", token: jwt });
const { items } = await mvAuth.listAgents();
const run = await mvAuth.runAgent(items[0].id, { message: "Summarize today's tickets" });
```

## Methods

| Method | Endpoint | Auth |
|---|---|---|
| `serve(id, { question, k? })` | `POST /serve/{id}` | deployment key |
| `query({ question, k? })` | `POST /query` | token |
| `runPipeline(id, { question, k? })` | `POST /pipelines/{id}/run` | token |
| `runAgent(id, { message, k? })` | `POST /agents/{id}/run` | token |
| `listPipelines()` / `listAgents()` | `GET /pipelines` · `/agents` | token |
| `crawl({ url, max_pages?, same_domain? })` | `POST /knowledge/crawl` | token |

Errors throw `MetaVitaError` with `.status` and `.message`.
