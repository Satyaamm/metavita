/**
 * Pure graph utilities — node creation, client-side validation (mirrors the
 * backend), and the empty graph. The stored graph IS the xyflow {nodes, edges}.
 */
import { NODE_TYPES } from "./nodes";

export interface GraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export interface PipelineGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const EMPTY_GRAPH: PipelineGraph = { nodes: [], edges: [] };

/** Create a node of `type` at `position`. `idFn` is injectable for deterministic tests. */
export function makeNode(
  type: string,
  position: { x: number; y: number } = { x: 0, y: 0 },
  idFn: () => string = () => crypto.randomUUID(),
): GraphNode {
  return { id: idFn(), type, position, data: { label: NODE_TYPES[type]?.label ?? type } };
}

/** Mirror of metavita_runtime.graph.validate_graph — returns error strings. */
export function validateGraph(graph: PipelineGraph): string[] {
  const errors: string[] = [];
  if (!graph || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) {
    return ["graph must have node and edge lists"];
  }
  const ids = new Set<string>();
  graph.nodes.forEach((n, i) => {
    if (!n.id) errors.push(`node[${i}] missing id`);
    else if (ids.has(n.id)) errors.push(`duplicate node id: ${n.id}`);
    else ids.add(n.id);
    if (!(n.type in NODE_TYPES)) errors.push(`node[${i}] unknown type: ${n.type}`);
  });
  graph.edges.forEach((e, j) => {
    if (!ids.has(e.source)) errors.push(`edge[${j}] source not found: ${e.source}`);
    if (!ids.has(e.target)) errors.push(`edge[${j}] target not found: ${e.target}`);
  });
  return errors;
}

export const isValidGraph = (graph: PipelineGraph): boolean => validateGraph(graph).length === 0;
