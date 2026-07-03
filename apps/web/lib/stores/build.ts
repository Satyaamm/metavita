/** Build-domain Zustand stores — pipelines and agents. */
import { create } from "zustand";
import { type AgentItem, type PipelineItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface PipelinesState {
  items: PipelineItem[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (name: string) => Promise<PipelineItem>;
}

export const usePipelinesStore = create<PipelinesState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listPipelines();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (name) => {
    const p = await api.createPipeline({ name });
    set((s) => ({ items: [p, ...s.items] }));
    return p;
  },
}));

interface AgentsState {
  items: AgentItem[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (name: string) => Promise<AgentItem>;
}

export const useAgentsStore = create<AgentsState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listAgents();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (name) => {
    const a = await api.createAgent({ name });
    set((s) => ({ items: [a, ...s.items] }));
    return a;
  },
}));
