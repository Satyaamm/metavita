/** Deployments Zustand store. */
import { create } from "zustand";
import { type DeploymentCreated, type DeploymentItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface DeploymentsState {
  items: DeploymentItem[];
  total: number;
  status: AsyncStatus;
  error?: string;
  fetch: (params?: { limit?: number; offset?: number }) => Promise<void>;
  create: (body: {
    name: string;
    target_type: "pipeline" | "agent";
    target_id: string;
  }) => Promise<DeploymentCreated>;
  setStatus: (id: string, status: "active" | "paused") => Promise<void>;
}

export const useDeploymentsStore = create<DeploymentsState>((set) => ({
  items: [],
  total: 0,
  status: "loading",
  fetch: async (params = {}) => {
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listDeployments(params);
      set({ items: r.items, total: r.total, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (body) => {
    const d = await api.createDeployment(body);
    set((s) => ({ items: [d, ...s.items], total: s.total + 1 }));
    return d;
  },
  setStatus: async (id, status) => {
    const updated =
      status === "paused" ? await api.pauseDeployment(id) : await api.unpauseDeployment(id);
    set((s) => ({ items: s.items.map((d) => (d.id === id ? updated : d)) }));
  },
}));
