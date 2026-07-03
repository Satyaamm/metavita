"""Public serving endpoint — runs a deployment, authenticated by its API key.

This is the customer-facing surface the embeddable widget / API consumers call.
Auth is the deployment's bearer key (not a session), so it does not use the
workspace dependency; the workspace comes from the deployment record.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..factory import ProviderFactory
from ..repositories import DeploymentRepository, RunRepository
from ..security.keys import verify_key
from ..services.run import execute_rag_run
from ..vectorstores import resolve_vector_store

router = APIRouter(prefix="/serve", tags=["serve"])

# The widget calls /serve from arbitrary customer origins; auth is a bearer key
# (no cookies), so wildcard CORS is safe here.
_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
}


class ServeRequest(BaseModel):
    question: str
    k: int = 5


@router.options("/{deployment_id}")
async def serve_preflight(deployment_id: uuid.UUID) -> Response:
    return Response(status_code=204, headers=_CORS)


@router.post("/{deployment_id}")
async def serve(
    deployment_id: uuid.UUID,
    body: ServeRequest,
    response: Response,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> dict:
    response.headers.update(_CORS)
    deployment = await DeploymentRepository(session).get_for_serving(deployment_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="deployment not found")

    token = authorization.removeprefix("Bearer ").strip()
    if not token or not verify_key(token, deployment.key_hash):
        raise HTTPException(status_code=401, detail="invalid api key")
    if deployment.status != "active":
        raise HTTPException(status_code=403, detail="deployment is paused")

    factory = ProviderFactory(
        get_settings(), session=session, workspace_id=deployment.workspace_id
    )
    embedder, embedding_model = await factory.embedding()
    chat, chat_model = await factory.chat()
    store = await resolve_vector_store(session, deployment.workspace_id)
    runs = RunRepository(session)

    run = await runs.start(
        workspace_id=deployment.workspace_id,
        pipeline_id=deployment.target_id if deployment.target_type == "pipeline" else None,
        kind="deployment",
        input={"question": body.question, "k": body.k, "deployment_id": str(deployment_id)},
    )
    started = time.perf_counter()

    async def record(**span) -> None:
        await runs.add_span(run, **span)

    try:
        out = await execute_rag_run(
            question=body.question,
            k=body.k,
            embedder=embedder,
            embedding_model=embedding_model,
            chat=chat,
            chat_model=chat_model,
            store=store,
            workspace_id=str(deployment.workspace_id),
            record=record,
        )
    except Exception as exc:  # noqa: BLE001
        await runs.finish(
            run,
            status="failed",
            output={"error": str(exc)},
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        await session.commit()
        raise HTTPException(status_code=500, detail="run failed") from exc

    await runs.finish(
        run,
        status="succeeded",
        output={"answer": out.answer, "citations": out.citations},
        latency_ms=int((time.perf_counter() - started) * 1000),
        tokens_in=out.tokens_in,
        tokens_out=out.tokens_out,
    )
    await session.commit()
    return {"answer": out.answer, "citations": out.citations, "run_id": str(run.id)}
