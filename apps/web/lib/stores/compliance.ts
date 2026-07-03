/** Compliance-domain Zustand store — GDPR DSAR jobs + retention policy. */
import { create } from "zustand";
import { type DSARItem, type RetentionPolicy, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface ComplianceState {
  requests: DSARItem[];
  retention: RetentionPolicy | null;
  status: AsyncStatus;
  error?: string;
  fetch: () => Promise<void>;
  createRequest: (body: { subject: string; kind: "export" | "erasure" }) => Promise<DSARItem>;
  process: (id: string) => Promise<void>;
  saveRetention: (body: {
    retention_days?: number;
    region?: string;
    hipaa?: boolean;
  }) => Promise<void>;
}

export const useComplianceStore = create<ComplianceState>((set, get) => ({
  requests: [],
  retention: null,
  status: "idle",
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const [reqs, ret] = await Promise.all([api.listDSARs(), api.getRetention()]);
      set({ requests: reqs.items, retention: ret, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  createRequest: async (body) => {
    const d = await api.createDSAR(body);
    set((s) => ({ requests: [d, ...s.requests] }));
    return d;
  },
  process: async (id) => {
    const d = await api.processDSAR(id);
    set((s) => ({ requests: s.requests.map((r) => (r.id === id ? d : r)) }));
  },
  saveRetention: async (body) => {
    const ret = await api.updateRetention(body);
    set({ retention: ret });
  },
}));
