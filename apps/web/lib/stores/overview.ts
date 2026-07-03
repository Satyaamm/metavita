/** Dashboard Zustand stores — real workspace stats and recent audit activity. */
import { create } from "zustand";
import { type Analytics, type AuditEvent, type OverviewStats, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface AnalyticsState {
  data: Analytics | null;
  status: AsyncStatus;
  fetch: (days?: number) => Promise<void>;
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  data: null,
  status: "loading",
  fetch: async (days = 14) => {
    set({ status: "loading" });
    try {
      set({ data: await api.getAnalytics(days), status: "ready" });
    } catch {
      set({ status: "error" });
    }
  },
}));

interface OverviewState {
  stats: OverviewStats | null;
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
}

export const useOverviewStore = create<OverviewState>((set) => ({
  stats: null,
  status: "idle",
  fetch: async () => {
    set({ status: "loading", error: undefined });
    try {
      const stats = await api.getStats();
      set({ stats, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
}));

interface AuditState {
  items: AuditEvent[];
  total: number;
  status: AsyncStatus;
  error?: string;
  fetch: (params?: { limit?: number; offset?: number }) => Promise<void>;
}

export const useAuditStore = create<AuditState>((set) => ({
  items: [],
  total: 0,
  status: "idle",
  fetch: async (params = { limit: 12 }) => {
    set({ status: "loading", error: undefined });
    try {
      const r = await api.listAudit(params);
      set({ items: r.items, total: r.total, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
}));
