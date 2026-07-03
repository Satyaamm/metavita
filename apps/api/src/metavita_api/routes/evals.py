"""Evals API — datasets and scored runs through a pipeline."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_workspace_id
from ..factory import ProviderFactory
from ..models import EvalDataset, EvalRun
from ..repositories import (
    EvalDatasetRepository,
    EvalRunRepository,
    PipelineRepository,
)
from ..services.run import execute_rag_run
from ..services.scoring import score_item, summarize
from ..vectorstore import PgVectorStore

router = APIRouter(tags=["evals"])


def _dataset(d: EvalDataset) -> dict:
    return {
        "id": str(d.id),
        "name": d.name,
        "items": d.items,
        "item_count": len(d.items),
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _eval_run(r: EvalRun, *, with_results: bool = False) -> dict:
    data = {
        "id": str(r.id),
        "dataset_id": str(r.dataset_id),
        "pipeline_id": str(r.pipeline_id) if r.pipeline_id else None,
        "status": r.status,
        "summary": r.summary,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }
    if with_results:
        data["results"] = r.results
    return data


class EvalItem(BaseModel):
    question: str
    expected: str | None = None


class DatasetCreate(BaseModel):
    name: str
    items: list[EvalItem]


class RunEvalRequest(BaseModel):
    pipeline_id: uuid.UUID
    k: int = 5


@router.get("/evals")
async def list_datasets(
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    items = await EvalDatasetRepository(session).list(workspace_id)
    return {"items": [_dataset(d) for d in items]}


@router.post("/evals", status_code=201)
async def create_dataset(
    body: DatasetCreate,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    dataset = await EvalDatasetRepository(session).create(
        workspace_id=workspace_id,
        name=body.name,
        items=[i.model_dump() for i in body.items],
    )
    await session.commit()
    return _dataset(dataset)


@router.get("/evals/{dataset_id}")
async def get_dataset(
    dataset_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    dataset = await EvalDatasetRepository(session).get(dataset_id, workspace_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return _dataset(dataset)


@router.get("/evals/{dataset_id}/runs")
async def list_eval_runs(
    dataset_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    runs = await EvalRunRepository(session).list_for_dataset(dataset_id, workspace_id)
    return {"items": [_eval_run(r) for r in runs]}


@router.post("/evals/{dataset_id}/run")
async def run_eval(
    dataset_id: uuid.UUID,
    body: RunEvalRequest,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    dataset = await EvalDatasetRepository(session).get(dataset_id, workspace_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    pipeline = await PipelineRepository(session).get(body.pipeline_id, workspace_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="pipeline not found")

    factory = ProviderFactory(get_settings(), session=session, workspace_id=workspace_id)
    embedder, embedding_model = await factory.embedding()
    chat, chat_model = await factory.chat()
    store = PgVectorStore(session)

    async def _noop(**_span) -> None:  # eval runs don't record per-step spans
        return None

    results: list[dict] = []
    for item in dataset.items:
        question = item.get("question", "")
        expected = item.get("expected")
        t = time.perf_counter()
        out = await execute_rag_run(
            question=question,
            k=body.k,
            embedder=embedder,
            embedding_model=embedding_model,
            chat=chat,
            chat_model=chat_model,
            store=store,
            workspace_id=str(workspace_id),
            record=_noop,
        )
        results.append(
            {
                "question": question,
                "expected": expected,
                "answer": out.answer,
                "score": score_item(
                    expected=expected, answer=out.answer, citations_count=len(out.citations)
                ),
                "latency_ms": int((time.perf_counter() - t) * 1000),
            }
        )

    eval_run = await EvalRunRepository(session).create(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        pipeline_id=body.pipeline_id,
        status="succeeded",
        summary=summarize(results),
        results=results,
    )
    await session.commit()
    return _eval_run(eval_run, with_results=True)


@router.get("/eval-runs/{run_id}")
async def get_eval_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    workspace_id: uuid.UUID = Depends(current_workspace_id),
) -> dict:
    run = await EvalRunRepository(session).get(run_id, workspace_id)
    if run is None:
        raise HTTPException(status_code=404, detail="eval run not found")
    return _eval_run(run, with_results=True)
