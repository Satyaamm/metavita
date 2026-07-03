# metavita (Python SDK)

Official Python SDK for the [MetaVita](../../README.md) agentic RAG platform — a thin, typed async client over the REST API.

## Install

```bash
pip install metavita
```

## Usage

```python
import asyncio
from metavita import MetaVita

async def main():
    # Public serving surface — authenticate with a deployment key.
    async with MetaVita("https://api.metavita.dev", api_key="mv_...") as mv:
        res = await mv.serve(deployment_id, question="What changed in v2?")
        print(res.answer, res.citations)

    # Authenticated builder API — authenticate with a workspace JWT.
    async with MetaVita("https://api.metavita.dev", token=jwt) as mv:
        agents = await mv.list_agents()
        run = await mv.run_agent(agents[0]["id"], message="Summarize today's tickets")

asyncio.run(main())
```

## Methods

| Method | Endpoint | Auth |
|---|---|---|
| `serve(id, question=, k=)` | `POST /serve/{id}` | deployment key |
| `query(question=, k=)` | `POST /query` | token |
| `run_pipeline(id, question=, k=)` | `POST /pipelines/{id}/run` | token |
| `run_agent(id, message=, k=)` | `POST /agents/{id}/run` | token |
| `list_pipelines()` / `list_agents()` | `GET /pipelines` · `/agents` | token |
| `crawl(url=, max_pages=, same_domain=, name=)` | `POST /knowledge/crawl` | token |

Errors raise `MetaVitaError` with `.status` and `.message`.
