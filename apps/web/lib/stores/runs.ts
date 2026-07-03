/** Runs / traces Zustand store. */
import { create } from "zustand";
import { type RunItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface RunsState {
  items: RunItem[];
  total: number;
  status: AsyncStatus;
  error?: string;
  fetch: (params?: { limit?: number; offset?: number }) => Promise<void>;
}

export const useRunsStore = create<RunsState>((set) => ({
  items: [],
  total: 0,
  status: "loading",
  fetch: async (params = {}) => {
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listRuns(params);
      set({ items: r.items, total: r.total, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
}));
