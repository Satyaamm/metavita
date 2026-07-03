/** Connections-domain Zustand store — BYO integrations + the provider catalog. */
import { create } from "zustand";
import { type ConnectionCatalog, type ConnectionItem, api } from "../api";
import type { AsyncStatus } from "./knowledge";

interface ConnectionsState {
  items: ConnectionItem[];
  catalog: ConnectionCatalog | null;
  status: AsyncStatus;
  error?: string;
  testing: Record<string, boolean>;
  fetch: () => Promise<void>;
  create: (body: {
    name: string;
    capability: string;
    provider: string;
    values: Record<string, unknown>;
  }) => Promise<ConnectionItem>;
  update: (id: string, body: { name?: string; values?: Record<string, unknown> }) => Promise<void>;
  test: (id: string) => Promise<{ ok: boolean; message: string }>;
  remove: (id: string) => Promise<void>;
}

export const useConnectionsStore = create<ConnectionsState>((set, get) => ({
  items: [],
  catalog: null,
  status: "idle",
  testing: {},
  fetch: async () => {
    if (get().status === "loading") return;
    set({ status: "loading", error: undefined });
    try {
      const [catalog, list] = await Promise.all([
        api.getConnectionCatalog(),
        api.listConnections(),
      ]);
      set({ catalog, items: list.items, status: "ready" });
    } catch (e) {
      set({ status: "error", error: String(e) });
    }
  },
  create: async (body) => {
    const conn = await api.createConnection(body);
    set((s) => ({ items: [conn, ...s.items] }));
    return conn;
  },
  update: async (id, body) => {
    const conn = await api.updateConnection(id, body);
    set((s) => ({ items: s.items.map((c) => (c.id === id ? conn : c)) }));
  },
  test: async (id) => {
    set((s) => ({ testing: { ...s.testing, [id]: true } }));
    try {
      const r = await api.testConnection(id);
      set((s) => ({
        items: s.items.map((c) =>
          c.id === id ? { ...c, status: r.status, status_detail: r.message } : c,
        ),
      }));
      return { ok: r.ok, message: r.message };
    } finally {
      set((s) => ({ testing: { ...s.testing, [id]: false } }));
    }
  },
  remove: async (id) => {
    await api.deleteConnection(id);
    set((s) => ({ items: s.items.filter((c) => c.id !== id) }));
  },
}));
