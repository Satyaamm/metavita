/** Prompts-domain Zustand store — versioned reusable prompt library. */
import { create } from "zustand";
import { type PromptItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface PromptsState {
  items: PromptItem[];
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  create: (body: { name: string; description?: string; content?: string }) => Promise<PromptItem>;
  remove: (id: string) => Promise<void>;
}

export const usePromptsStore = create<PromptsState>((set, get) => ({
  items: [],
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listPrompts();
      set({ items: r.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (body) => {
    const p = await api.createPrompt(body);
    set((s) => ({ items: [p, ...s.items] }));
    return p;
  },
  remove: async (id) => {
    await api.deletePrompt(id);
    set((s) => ({ items: s.items.filter((it) => it.id !== id) }));
  },
}));
