/** Tools-domain Zustand store — the registry of agent-callable tools. */
import { create } from "zustand";
import { type ToolItem, type ToolKind, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface NewTool {
  name: string;
  kind: ToolKind;
  description: string;
  config: Record<string, unknown>;
  input_schema: Record<string, unknown>;
}

interface ToolsState {
  items: ToolItem[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (body: NewTool) => Promise<ToolItem>;
  toggle: (id: string, enabled: boolean) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export const useToolsStore = create<ToolsState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listTools();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (body) => {
    const t = await api.createTool(body);
    set((s) => ({ items: [t, ...s.items] }));
    return t;
  },
  toggle: async (id, enabled) => {
    const t = await api.updateTool(id, { enabled });
    set((s) => ({ items: s.items.map((it) => (it.id === id ? t : it)) }));
  },
  remove: async (id) => {
    await api.deleteTool(id);
    set((s) => ({ items: s.items.filter((it) => it.id !== id) }));
  },
}));
