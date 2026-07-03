/**
 * Pipeline node-type registry (frontend) — mirrors the backend NODE_TYPES in
 * metavita_runtime.graph. Drives the xyflow palette and node rendering.
 */
export type NodeCategory = "source" | "transform" | "retrieve" | "reason" | "tool" | "output";

export interface NodeTypeDef {
  type: string;
  category: NodeCategory;
  label: string;
  description: string;
}

export const NODE_TYPES: Record<string, NodeTypeDef> = {
  source: { type: "source", category: "source", label: "Data Source", description: "An index or uploaded corpus" },
  chunk: { type: "chunk", category: "transform", label: "Chunk", description: "Split text into chunks" },
  embed: { type: "embed", category: "transform", label: "Embed", description: "Vectorize chunks" },
  retrieve: { type: "retrieve", category: "retrieve", label: "Retrieve", description: "Vector / hybrid search" },
  rerank: { type: "rerank", category: "retrieve", label: "Rerank", description: "Reorder by relevance" },
  llm: { type: "llm", category: "reason", label: "LLM", description: "Generate an answer" },
  router: { type: "router", category: "reason", label: "Router", description: "Branch on a condition" },
  tool: { type: "tool", category: "tool", label: "Tool", description: "Call an external tool" },
  output: { type: "output", category: "output", label: "Output", description: "Return the result" },
};

export const PALETTE: { category: NodeCategory; label: string; types: string[] }[] = [
  { category: "source", label: "Sources", types: ["source"] },
  { category: "transform", label: "Transform", types: ["chunk", "embed"] },
  { category: "retrieve", label: "Retrieve", types: ["retrieve", "rerank"] },
  { category: "reason", label: "Reason", types: ["llm", "router"] },
  { category: "tool", label: "Tools", types: ["tool"] },
  { category: "output", label: "Output", types: ["output"] },
];

export const CATEGORY_TINT: Record<NodeCategory, string> = {
  source: "#E9E3F6",
  transform: "#DCE2F6",
  retrieve: "#E6EDD9",
  reason: "#FBE7D2",
  tool: "#F2DCEC",
  output: "#E6E9EB",
};
