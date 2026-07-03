"""Agent ReAct loop tests (pure, with fakes)."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from metavita_api.services.agent import build_tools, make_tool_executor, run_agent
from metavita_providers import EmbeddingResult, ToolCall, ToolTurn
from metavita_runtime.types import RetrievedChunk


class ScriptedChat:
    """Returns a tool call on the first turn, then a final answer."""

    def __init__(self) -> None:
        self.calls = 0

    async def chat_tools(self, messages, *, model, tools, system=None, max_tokens=1024) -> ToolTurn:
        self.calls += 1
        if self.calls == 1:
            return ToolTurn(
                text="Let me search.",
                tool_calls=[ToolCall(id="t1", name="retriever", input={"query": "sky"})],
                stop_reason="tool_use",
            )
        return ToolTurn(text="The sky is blue [1].", tool_calls=[], stop_reason="end_turn")


class FakeEmbed:
    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        return EmbeddingResult([[0.1, 0.2, 0.3] for _ in texts], "fake", 3)


class FakeStore:
    async def search(self, query_vector, *, k, workspace_id, query_text=None):
        return [RetrievedChunk(text="The sky is blue.", score=0.9, document_id="d1", chunk_index=0)]


def test_build_tools_only_retriever() -> None:
    assert [t.name for t in build_tools(["retriever", "web_search"])] == ["retriever"]
    assert build_tools(["web_search"]) == []


@pytest.mark.asyncio
async def test_tool_executor_retriever_and_unknown() -> None:
    execute = make_tool_executor(
        embedder=FakeEmbed(), embedding_model="f", store=FakeStore(), workspace_id="ws"
    )
    out = await execute(ToolCall(id="t1", name="retriever", input={"query": "sky"}))
    assert "[1] The sky is blue." in out
    miss = await execute(ToolCall(id="t2", name="http_request", input={}))
    assert "not available" in miss


@pytest.mark.asyncio
async def test_run_agent_executes_tool_then_answers() -> None:
    spans: list[dict] = []

    async def record(**kw) -> None:
        spans.append(kw)

    execute = make_tool_executor(
        embedder=FakeEmbed(), embedding_model="f", store=FakeStore(), workspace_id="ws"
    )
    answer = await run_agent(
        system="sys",
        message="what color is the sky?",
        chat=ScriptedChat(),
        chat_model="fake",
        tools=build_tools(["retriever"]),
        execute=execute,
        record=record,
    )
    assert answer == "The sky is blue [1]."
    assert [s["node_type"] for s in spans] == ["llm", "tool", "llm"]
    assert spans[1]["name"] == "tool:retriever"
