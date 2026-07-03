/**
 * Feature-flag registry — single source of truth for gating not-yet-shipped or
 * optional features. Defaults live here; runtime state is held in the Zustand UI
 * store (lib/stores/ui.ts) so flags can be toggled (e.g. a dev panel) and read via
 * `useFlag(key)`. Disabled features render as "coming soon"/disabled, not hidden.
 */

export type FlagKey =
  | "webCrawl"
  | "connectors"
  | "videoIngestion"
  | "evals"
  | "pipelineBuilder"
  | "agentBuilder";

export const FLAG_DEFAULTS: Record<FlagKey, boolean> = {
  webCrawl: false,
  connectors: false,
  videoIngestion: false,
  evals: false,
  pipelineBuilder: false,
  agentBuilder: false,
};

export const FLAG_LABELS: Record<FlagKey, string> = {
  webCrawl: "Web crawling",
  connectors: "Connectors (Drive, Notion, S3…)",
  videoIngestion: "Video ingestion",
  evals: "Evals",
  pipelineBuilder: "Visual pipeline builder",
  agentBuilder: "Agent builder",
};
