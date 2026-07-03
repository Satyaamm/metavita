"""Pipeline graph: node-type registry + pure validation.

A pipeline is a DAG serialized as ``{"nodes": [...], "edges": [...]}`` — the same
shape the visual builder (xyflow) emits and the API stores. This module is pure and
unit-testable; the executor (later) consumes validated graphs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeType:
    type: str
    category: str  # source | transform | retrieve | reason | tool | output
    label: str


#: Registry of known node types (kept in sync with the frontend node registry).
NODE_TYPES: dict[str, NodeType] = {
    "source": NodeType("source", "source", "Data Source"),
    "chunk": NodeType("chunk", "transform", "Chunk"),
    "embed": NodeType("embed", "transform", "Embed"),
    "retrieve": NodeType("retrieve", "retrieve", "Retrieve"),
    "rerank": NodeType("rerank", "retrieve", "Rerank"),
    "llm": NodeType("llm", "reason", "LLM"),
    "router": NodeType("router", "reason", "Router"),
    "tool": NodeType("tool", "tool", "Tool"),
    "output": NodeType("output", "output", "Output"),
}


def validate_graph(graph: object) -> list[str]:
    """Return a list of validation errors; empty means the graph is valid."""
    errors: list[str] = []
    if not isinstance(graph, dict):
        return ["graph must be an object"]

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list):
        errors.append("graph.nodes must be a list")
        nodes = []
    if not isinstance(edges, list):
        errors.append("graph.edges must be a list")
        edges = []

    ids: set[str] = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node[{i}] must be an object")
            continue
        nid = node.get("id")
        ntype = node.get("type")
        if not nid:
            errors.append(f"node[{i}] missing id")
        elif nid in ids:
            errors.append(f"duplicate node id: {nid}")
        else:
            ids.add(nid)
        if ntype not in NODE_TYPES:
            errors.append(f"node[{i}] unknown type: {ntype}")

    for j, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge[{j}] must be an object")
            continue
        if edge.get("source") not in ids:
            errors.append(f"edge[{j}] source not found: {edge.get('source')}")
        if edge.get("target") not in ids:
            errors.append(f"edge[{j}] target not found: {edge.get('target')}")

    return errors


def is_valid_graph(graph: object) -> bool:
    return not validate_graph(graph)


def topological_order(graph: dict) -> list[str]:
    """Return node ids in execution order (Kahn). On a cycle, returns a partial
    order shorter than the node count — see `has_cycle`."""
    nodes = [
        n["id"] for n in graph.get("nodes", []) if isinstance(n, dict) and n.get("id")
    ]
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    indeg: dict[str, int] = dict.fromkeys(nodes, 0)
    for e in graph.get("edges", []):
        if not isinstance(e, dict):
            continue
        s, t = e.get("source"), e.get("target")
        if s in adj and t in indeg:
            adj[s].append(t)
            indeg[t] += 1

    queue = [n for n in nodes if indeg[n] == 0]
    order: list[str] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    return order


def has_cycle(graph: dict) -> bool:
    node_count = sum(
        1 for n in graph.get("nodes", []) if isinstance(n, dict) and n.get("id")
    )
    return len(topological_order(graph)) != node_count


EMPTY_GRAPH: dict = {"nodes": [], "edges": []}
