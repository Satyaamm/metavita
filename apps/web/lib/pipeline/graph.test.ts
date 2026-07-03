import { describe, expect, it } from "vitest";
import { NODE_TYPES } from "./nodes";
import { type PipelineGraph, isValidGraph, makeNode, validateGraph } from "./graph";

let counter = 0;
const seqId = () => `n${++counter}`;

describe("makeNode", () => {
  it("creates a node with type, label, and id", () => {
    const node = makeNode("llm", { x: 10, y: 20 }, () => "fixed-id");
    expect(node).toMatchObject({
      id: "fixed-id",
      type: "llm",
      position: { x: 10, y: 20 },
      data: { label: NODE_TYPES.llm.label },
    });
  });
});

describe("validateGraph", () => {
  it("accepts an empty graph", () => {
    expect(isValidGraph({ nodes: [], edges: [] })).toBe(true);
  });

  it("accepts a valid linear pipeline", () => {
    counter = 0;
    const a = makeNode("source", { x: 0, y: 0 }, seqId);
    const b = makeNode("retrieve", { x: 0, y: 0 }, seqId);
    const c = makeNode("output", { x: 0, y: 0 }, seqId);
    const graph: PipelineGraph = {
      nodes: [a, b, c],
      edges: [
        { id: "e1", source: a.id, target: b.id },
        { id: "e2", source: b.id, target: c.id },
      ],
    };
    expect(validateGraph(graph)).toEqual([]);
  });

  it("flags an unknown node type", () => {
    const graph = { nodes: [{ id: "a", type: "wormhole", position: { x: 0, y: 0 }, data: {} }], edges: [] };
    expect(validateGraph(graph).some((e) => e.includes("unknown type"))).toBe(true);
  });

  it("flags a dangling edge", () => {
    const graph: PipelineGraph = {
      nodes: [{ id: "a", type: "source", position: { x: 0, y: 0 }, data: {} }],
      edges: [{ id: "e", source: "a", target: "ghost" }],
    };
    expect(validateGraph(graph).some((e) => e.includes("target not found"))).toBe(true);
  });

  it("flags duplicate node ids", () => {
    const graph: PipelineGraph = {
      nodes: [
        { id: "a", type: "source", position: { x: 0, y: 0 }, data: {} },
        { id: "a", type: "output", position: { x: 0, y: 0 }, data: {} },
      ],
      edges: [],
    };
    expect(validateGraph(graph).some((e) => e.includes("duplicate node id"))).toBe(true);
  });
});
