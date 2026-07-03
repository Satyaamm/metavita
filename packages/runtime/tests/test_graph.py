"""Pipeline graph validation tests."""

from __future__ import annotations

from metavita_runtime import (
    NODE_TYPES,
    has_cycle,
    is_valid_graph,
    topological_order,
    validate_graph,
)


def test_empty_graph_is_valid() -> None:
    assert validate_graph({"nodes": [], "edges": []}) == []
    assert is_valid_graph({"nodes": [], "edges": []})


def test_valid_linear_pipeline() -> None:
    graph = {
        "nodes": [
            {"id": "n1", "type": "source"},
            {"id": "n2", "type": "retrieve"},
            {"id": "n3", "type": "llm"},
            {"id": "n4", "type": "output"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
        ],
    }
    assert is_valid_graph(graph)


def test_unknown_node_type() -> None:
    errors = validate_graph({"nodes": [{"id": "a", "type": "wormhole"}], "edges": []})
    assert any("unknown type" in e for e in errors)


def test_duplicate_node_id() -> None:
    errors = validate_graph(
        {"nodes": [{"id": "a", "type": "source"}, {"id": "a", "type": "output"}], "edges": []}
    )
    assert any("duplicate node id" in e for e in errors)


def test_dangling_edge() -> None:
    errors = validate_graph(
        {"nodes": [{"id": "a", "type": "source"}], "edges": [{"source": "a", "target": "ghost"}]}
    )
    assert any("target not found" in e for e in errors)


def test_non_object_graph() -> None:
    assert validate_graph(["not", "a", "graph"]) == ["graph must be an object"]


def test_registry_has_core_types() -> None:
    for t in ("source", "retrieve", "llm", "output"):
        assert t in NODE_TYPES


def test_topological_order_linear() -> None:
    graph = {
        "nodes": [
            {"id": "a", "type": "source"},
            {"id": "b", "type": "retrieve"},
            {"id": "c", "type": "llm"},
        ],
        "edges": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}],
    }
    assert topological_order(graph) == ["a", "b", "c"]
    assert has_cycle(graph) is False


def test_topological_order_detects_cycle() -> None:
    graph = {
        "nodes": [{"id": "a", "type": "source"}, {"id": "b", "type": "llm"}],
        "edges": [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}],
    }
    assert has_cycle(graph) is True
