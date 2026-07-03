"""Agent executor — a ReAct tool loop.

The agent plans with the LLM (`chat_tools`); when it requests a tool, we execute it
and feed the result back, repeating until the model answers or a step cap is hit. A
span is recorded per step. The only real tool today is `retriever` (vector search over
the workspace); others report as unavailable. Decoupled from persistence via `record`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

from metavita_providers import (
    AgentMessage,
    ChatProvider,
    EmbeddingProvider,
    ToolCall,
    ToolDef,
    ToolResult,
)
from metavita_runtime import VectorStore

DEFAULT_SYSTEM = (
    "You are a MetaVita agent. Use the available tools to gather grounding before "
    "answering, and cite retrieved passages with markers like [1]. If a tool reports "
    "it is unavailable, answer as best you can without it."
)

RETRIEVER = ToolDef(
    name="retriever",
    description=(
        "Search the workspace knowledge base for passages relevant to a query. "
        "Call this to ground your answer in the user's documents."
    ),
    input_schema={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to search for"}},
        "required": ["query"],
    },
)

ToolExecutor = Callable[[ToolCall], Awaitable[str]]
SpanRecorder = Callable[..., Awaitable[None]]


def build_tools(enabled: Sequence[str]) -> list[ToolDef]:
    """Map an agent's enabled tool keys to tool definitions (MVP: retriever only)."""
    tools: list[ToolDef] = []
    if "retriever" in enabled:
        tools.append(RETRIEVER)
    return tools


def make_tool_executor(
    *,
    embedder: EmbeddingProvider,
    embedding_model: str,
    store: VectorStore,
    workspace_id: str,
    k: int = 5,
) -> ToolExecutor:
    async def execute(call: ToolCall) -> str:
        if call.name == "retriever":
            query = str(call.input.get("query", ""))
            emb = await embedder.embed([query], model=embedding_model)
            chunks = await store.search(
                emb.vectors[0], k=k, workspace_id=workspace_id, query_text=query
            )
            return (
                "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))
                or "No relevant passages found."
            )
        return f"Tool '{call.name}' is not available in this environment."

    return execute


async def run_agent(
    *,
    system: str,
    message: str,
    chat: ChatProvider,
    chat_model: str,
    tools: Sequence[ToolDef],
    execute: ToolExecutor,
    record: SpanRecorder,
    max_steps: int = 6,
) -> str:
    messages: list[AgentMessage] = [AgentMessage(role="user", text=message)]
    final = ""
    for step in range(max_steps):
        turn = await chat.chat_tools(messages, model=chat_model, tools=tools, system=system)
        await record(
            seq=step * 2,
            name="agent step",
            node_type="llm",
            status="succeeded",
            latency_ms=None,
            detail={"tool_calls": [tc.name for tc in turn.tool_calls]},
        )
        final = turn.text
        if not turn.tool_calls:
            return turn.text

        messages.append(AgentMessage(role="assistant", text=turn.text, tool_calls=turn.tool_calls))
        results: list[ToolResult] = []
        for call in turn.tool_calls:
            output = await execute(call)
            await record(
                seq=step * 2 + 1,
                name=f"tool:{call.name}",
                node_type="tool",
                status="succeeded",
                latency_ms=None,
                detail={"input": call.input},
            )
            results.append(ToolResult(tool_use_id=call.id, content=output))
        messages.append(AgentMessage(role="user", tool_results=results))

    return final or "(reached step limit)"
